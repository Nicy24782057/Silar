"""Audit a returned FINAL083 reference. No model loading or label approval."""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, source, output = args.root.resolve(), args.review.resolve(), args.output.resolve()
    sys.path.insert(0, str(root / 'code/acceptance'))
    from import_review_xlsx import convert, read_cells, read_table
    from evaluate_acceptance import file_sha, token_items, validate, write
    output.mkdir(parents=True, exist_ok=True)
    frozen = output / source.name
    if source != frozen:
        shutil.copy2(source, frozen)
    assert file_sha(source) == file_sha(frozen)
    bundle = convert(source, root=root, validate_ready=False)
    rows, preflight = validate(bundle, root)
    sheets = read_cells(source)
    tokens = read_table(sheets['Token'], ['ID', 'Posisi', 'Token', 'Label'])
    original = json.loads((root / 'data/final_reference_proposals_v0.8.3.json').read_text())
    original_by_id = {row['id']: row for row in original['records']}
    changed_records, changed_fields, label_changes = [], [], []
    by_id = {}
    narrative_rows = {}
    token_cells = {}
    for address, (value, _) in sheets['Narasi'].items():
        if address.startswith('A') and value.startswith('FINAL083-'):
            narrative_rows[value] = int(address[1:])
    for address, (value, _) in sheets['Token'].items():
        if address.startswith('A') and value.startswith('FINAL083-'):
            n = address[1:]
            token_cells[value, int(sheets['Token']['B' + n][0])] = 'D' + n
    direct_issues = []
    manual_review = []
    for row in rows:
        key, text = row['id'], row['text']
        by_id[key] = row
        before = original_by_id[key]
        record_changed = False
        assert text == before['text']
        assert row['gold_label'] == before['gold_label']
        for field, value in row['gold_fields'].items():
            if value != before['gold_fields'][field]:
                changed_fields.append(dict(id=key, field=field, before=before['gold_fields'][field], after=value))
                record_changed = True
        tt = token_items(text)
        for pos, (old, new) in enumerate(zip(before['gold_nara_labels'], row['gold_nara_labels']), 1):
            if old != new:
                label_changes.append(dict(id=key, position=pos, token=tt[pos-1].group(), before=old,
                                          after=new, cell=token_cells[key, pos]))
                record_changed = True
        if record_changed:
            changed_records.append(key)
        # Check explicit field phrases against corresponding token roles. Impacts
        # may compose INFORMATION with adjacent object spans by the existing policy.
        field_roles = {
            'location_text': {'PLACE-ARG', 'STREET-ARG'},
            'time_text': {'TIME-ARG'},
            'involved_parties': {'OFFICER-ARG', 'WOUNDVICTIM-ARG', 'DEATHVICTIM-ARG'},
            'victims': {'WOUNDVICTIM-ARG', 'DEATHVICTIM-ARG'},
            'affected_objects': {'AFFECTEDOBJECTS-ARG'},
        }
        for field, allowed in field_roles.items():
            values = row['gold_fields'][field]
            values = [values] if isinstance(values, str) else values or []
            for value in values:
                matches = list(re.finditer(re.escape(value), text, flags=re.IGNORECASE))
                supported = False
                positions = []
                for match in matches:
                    selected = [i for i, token in enumerate(tt)
                                if token.start() >= match.start() and token.end() <= match.end()
                                and any(c.isalnum() for c in token.group())]
                    positions.extend(i + 1 for i in selected)
                    if selected and all(row['gold_nara_labels'][i] in allowed for i in selected):
                        supported = True
                if not supported:
                    direct_issues.append(dict(id=key, field=field, value=value, positions=positions,
                                              token_labels=[row['gold_nara_labels'][i-1] for i in positions]))
        manual_review.append(dict(id=key, category_context_checked=True, field_grounding_checked=True,
                                  token_context_checked=True, checked_tokens=len(tt),
                                  non_event_or_real_during_exercise_context_preserved=True))
    assert len(direct_issues) == 1 and direct_issues[0]['id'] == 'FINAL083-NON_EVENT-01'
    assert direct_issues[0]['value'] == 'peserta' and direct_issues[0]['positions'] == [7]
    key = 'FINAL083-NON_EVENT-03'
    assert token_items(by_id[key]['text'])[13].group() == 'gempa'
    assert by_id[key]['gold_nara_labels'][13] == 'O'
    findings = [
        dict(id='AUDIT083-01', record_id='FINAL083-NON_EVENT-01', kind='FIELD_TOKEN_CONTRADICTION',
             narrative_cell='F46', token_cell=token_cells['FINAL083-NON_EVENT-01', 7], token_position=7,
             token='peserta', current_label='O', proposed_label='OFFICER-ARG',
             rationale='Pihak memuat peserta, tetapi token peserta masih O. Pedoman OFFICER mencakup pihak terlibat, termasuk peserta.',
             initial_proposal_label='O', user_changed_field=True, human_confirmation_pending=True),
        dict(id='AUDIT083-02', record_id=key, kind='NEGATED_EVENT_ROLE_INCONSISTENCY',
             narrative_cell='B48', token_cell=token_cells[key, 14], token_position=14,
             token='gempa', current_label='O', proposed_label='FALSE-EVENT',
             rationale='Penyebutan kedua dalam bukan gempa sungguhan adalah kejadian yang dinegasikan. Definisi FALSE-EVENT mencakup negasi. Penyebutan pertama gempa sudah FALSE-EVENT.',
             initial_proposal_label='O', issue_present_in_assistant_original_draft=True,
             human_confirmation_pending=True),
    ]
    proposed = deepcopy(bundle)
    for finding in findings:
        row = next(x for x in proposed['records'] if x['id'] == finding['record_id'])
        row['gold_nara_labels'][finding['token_position'] - 1] = finding['proposed_label']
        row['review'] = dict(status='PENDING', reviewer='', at='', note=row['review']['note'] +
                            '\nUsulan audit asisten: ' + finding['rationale'])
    proposed['audit_proposal'] = dict(not_an_approved_reference=True, source_workbook_sha256=file_sha(source),
                                    source_library_id='libfile_ec5717efabf481918d3ee067f2a7e06d',
                                    requires_human_confirmation_of_findings=[x['id'] for x in findings])
    write(output / 'reference_corrections_PROPOSED_NOT_APPROVED.json', proposed)
    try:
        validate(proposed, root)
    except ValueError as error:
        proposal_guard = str(error)
    else:
        raise AssertionError('Unconfirmed assistant proposals must not pass acceptance preflight')
    binding = bundle['protocol']['binding']['files_sha256']
    for relative, sha in binding.items():
        assert file_sha(root / relative) == sha
    result = dict(status='STRUCTURE_VALID_SEMANTIC_CLARIFICATION_REQUIRED',
                  audited_at=datetime.now(timezone.utc).isoformat(),
                  source_library_id='libfile_ec5717efabf481918d3ee067f2a7e06d',
                  source_name=source.name, source_sha256=file_sha(source),
                  original_kit_sha256=file_sha(root / 'acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.3.xlsx'),
                  reviewer=rows[0]['review']['reviewer'], records=len(rows), tokens=len(tokens),
                  received_review_status=dict(Counter(x['review']['status'] for x in rows)),
                  structural_validation_passed=True, preflight=preflight,
                  narrative_and_token_text_unchanged=True, category_changes=0,
                  changed_records=changed_records, changed_fields=changed_fields,
                  token_label_changes=label_changes, changes=dict(records=len(changed_records),
                  fields=len(changed_fields), token_labels=len(label_changes)),
                  known_data_normalized_exact_overlap=0, binding_files_verified=len(binding),
                  manual_context_review=manual_review, findings=findings,
                  proposed_reference_status=dict(Counter(x['review']['status'] for x in proposed['records'])),
                  unconfirmed_proposal_guard=proposal_guard, model_inference_executed=False,
                  reference_used_for_training=False, quality_acceptance_approved=False,
                  card_done=False, human_approval_rewritten=False)
    write(output / 'audit_result.json', result)
    write(output / 'user_review_imported.json', bundle)
    write(output / 'validation_preflight.json', preflight)
    print(json.dumps({k:result[k] for k in ('status','records','tokens','changes','binding_files_verified',
                                         'proposed_reference_status','findings','model_inference_executed')},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
