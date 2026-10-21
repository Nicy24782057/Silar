"""Cache deterministic frozen BERT layers; never include new acceptance inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from train_sena_cpu import sha, write


def run(root, training, warm, output):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from safetensors.torch import save_file
    output.mkdir(parents=True, exist_ok=False)
    lock = json.loads((root/'config/quality_candidate_asset_lock_v0.8.2.json').read_text())
    assert sha(warm/'model.safetensors') == lock['models']['sena']['files']['model.safetensors']
    torch.set_num_threads(2)
    model = AutoModelForSequenceClassification.from_pretrained(warm, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(warm, local_files_only=True)
    model.eval()
    train = json.loads((training/'training_records_frozen.json').read_text())
    sets = json.loads((training/'scoring_sets_frozen.json').read_text())
    texts = list(dict.fromkeys(r['text'] for r in train + [r for rows in sets.values() for r in rows]))
    index, ids_to_key, inputs = {}, {}, []
    for text in texts:
        digest = hashlib.sha256(text.encode()).hexdigest()
        index[digest] = {}
        for cap in (192, 512):
            ids = tokenizer(text, truncation=True, max_length=cap)['input_ids']
            key = tuple(ids)
            if key not in ids_to_key:
                ids_to_key[key] = f'f{len(inputs):05d}'
                inputs.append(ids)
            index[digest][str(cap)] = ids_to_key[key]
    features = {}
    verification = []
    with torch.inference_mode():
        for offset in range(0, len(inputs), 16):
            batch = tokenizer.pad({'input_ids': inputs[offset:offset+16]}, padding=True, return_tensors='pt')
            mask = model.bert.get_extended_attention_mask(batch['attention_mask'], batch['input_ids'].shape)
            hidden = model.bert.embeddings(input_ids=batch['input_ids'], token_type_ids=batch.get('token_type_ids'))
            for layer in model.bert.encoder.layer[:-1]:
                hidden = layer(hidden, attention_mask=mask)[0]
            if offset in (0, 16, 32):
                final = model.bert.encoder.layer[-1](hidden, attention_mask=mask)[0]
                cached_probs = torch.softmax(model.classifier(model.dropout(model.bert.pooler(final))), -1)
                actual_probs = torch.softmax(model(**batch).logits, -1)
                delta = float((cached_probs-actual_probs).abs().max())
                assert delta <= 1e-5, delta
                verification.append({'batch_offset': offset, 'max_probability_delta': delta})
            for i, ids in enumerate(inputs[offset:offset+16]):
                features[f'f{offset+i:05d}'] = hidden[i, :len(ids)].clone().contiguous()
            if offset % 160 == 0:
                write(output/'progress.json', {'status': 'CACHING_FROZEN_LAYERS', 'completed': min(offset+16,len(inputs)), 'total': len(inputs)})
                print('Frozen prefix cached', min(offset+16,len(inputs)), '/', len(inputs), flush=True)
    save_file(features, output/'features.safetensors')
    write(output/'index.json', index)
    write(output/'manifest.json', dict(status='SUCCEEDED', inputs=len(inputs), source_texts=len(texts),
        warm_start_weight_sha256=sha(warm/'model.safetensors'), features_sha256=sha(output/'features.safetensors'),
        index_sha256=sha(output/'index.json'), full_forward_comparisons=verification,
        training_records_sha256=sha(training/'training_records_frozen.json'),
        scoring_sets_sha256=sha(training/'scoring_sets_frozen.json'),
        cached_layers='EMBEDDINGS_AND_ENCODER_0_TO_10_EVAL_MODE',
        independent_acceptance_inputs_read=False, new_gradient_training_executed=False))
    print('FROZEN_PREFIX_CACHE_SUCCEEDED', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root','training','warm','output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.training.resolve(), a.warm.resolve(), a.output.resolve())
