"""Verify immutable review, actual outputs, saved spreadsheets and pending guards."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
import zipfile
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/acceptance'))
from import_review_xlsx import read_cells,read_table,value,convert
from evaluate_acceptance import token_items


def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(output):
    original=ROOT/'evidence/acceptance_v081/original_run/evidence'
    frozen=load(original/'reviewed_bundle_frozen.json')
    before=load(ROOT/'evidence/acceptance_v081/scoring_completed/evaluation.json')
    final=ROOT/'evidence/field_fix_v082/replay_final'
    after=load(final/'reviewed50/evaluation.json')
    assert before['reference_file_sha256']==sha(original/'reviewed_bundle_frozen.json')
    assert before['predictions_sha256']==sha(original/'predictions.jsonl')
    assert sha(ROOT/'evidence/acceptance_v081/submission/Review_Penerimaan_Akhir_SLR09_v0.8.1.xlsx')=='2bc6e42c8111aa2fdc80206e6c0720a892c59000c4780733cd0831f7ea27cafc'
    for rel,h in frozen['protocol']['binding']['files_sha256'].items():
        assert sha(ROOT/'evidence/acceptance_v081/pre_inference_snapshot'/rel)==h
    for source,replay in [(original/'predictions.jsonl',final/'reviewed50/predictions.jsonl'),
                          (ROOT/'evidence/quality_fix_v081/guard_verification22b/predictions.jsonl',final/'previous50/predictions.jsonl')]:
        old=[json.loads(x) for x in source.read_text().splitlines()];new=[json.loads(x) for x in replay.read_text().splitlines()]
        assert len(old)==len(new)==50
        for p,q in zip(old,new):assert p['id']==q['id'] and p['event_classifier']==q['event_classifier'] and p['nara_tokens']==q['nara_tokens']
    report=read_cells(output/'SLR09_Hasil_Uji_dan_Perbaikan_v0.8.2.xlsx')
    # Report formulas are expected; the strict value() helper is for human
    # review inputs only and must continue rejecting formulas in that input.
    cached=lambda sheet,address:sheet.get(address,('',False))[0]
    s=report['Hasil'];assert abs(float(cached(s,'B13'))-163/207)<1e-14 and abs(float(cached(s,'C13'))-177/207)<1e-14
    assert cached(s,'E13')=='Belum' and cached(s,'F13')=='Memenuhi'
    assert [float(cached(s,x)) for x in ('B21','C21','B22','C22')]==[163,177,207,207]
    headers=['ID','Narasi','Acuan kelas','Prediksi SENA','Confidence','Flag <0,95','Reviewer','Keluarga','Catatan reviewer']
    rows=[dict(zip(headers,[cached(report['Narasi'],f'{chr(65+i)}{number}') for i in range(9)])) for number in range(6,56)]
    assert len(rows)==50 and {r['Reviewer'] for r in rows}=={'bintang'}
    assert [r['ID'] for r in rows]==[r['id'] for r in frozen['records']]
    for row,source in zip(rows,frozen['records']):assert row['Narasi']==source['text'] and row['Acuan kelas']==source['gold_label'] and row['Catatan reviewer']==source['review']['note']
    kit=output/'Review_Penerimaan_Akhir_SLR09_v0.8.2.xlsx';cells=read_cells(kit)
    assert not value(cells['Mulai'],'B5') and cached(cells['Mulai'],'B14')=='PERLU REVIEW ACUAN'
    rows=read_table(cells['Narasi'],['ID','Narasi','Kategori','Lokasi','Waktu','Pihak','Dampak','Korban','Objek','Status','Catatan'])
    tokens=read_table(cells['Token'],['ID','Posisi','Token','Label'])
    assert len(rows)==50 and Counter(r['Status'] for r in rows)=={'PENDING':50} and len(tokens)==671
    proposals=load(ROOT/'data/final_reference_proposals_v0.8.2.json');expected=[]
    for row,source in zip(rows,proposals['records']):
        assert row['ID']==source['id'] and row['Narasi']==source['text'] and row['Kategori']==source['gold_label']
        for i,(token,label) in enumerate(zip(token_items(source['text']),source['gold_nara_labels']),1):expected.append({'ID':source['id'],'Posisi':str(i),'Token':token.group(),'Label':label})
    assert tokens==expected
    try:convert(kit,root=ROOT)
    except ValueError as e:assert str(e)=='Isi nama reviewer pada Mulai!B5'
    else:raise AssertionError('Blank reviewer accepted')
    # This complete reviewer exists only in memory; no approval is saved.
    memory={k:dict(v) for k,v in cells.items()};memory['Mulai']['B5']=('FIXTURE ONLY',False)
    for i in range(6,56):memory['Narasi'][f'J{i}']=('APPROVED',False)
    with patch('import_review_xlsx.read_cells',return_value=memory):
        bundle=convert(kit,root=ROOT,validate_ready=True);assert len(bundle['records'])==50
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    for p in [kit,output/'SLR09_Hasil_Uji_dan_Perbaikan_v0.8.2.xlsx']:
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            if p==kit:
                for i in (2,3):
                    sheet=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
                    assert sheet.find('.//s:pane',ns) is not None and sheet.find('.//s:dataValidation',ns) is not None and sheet.find('.//s:tablePart',ns) is not None
        assert 'Cell search matched 0 entries.' in (output/(p.stem+'_formula_scan.ndjson')).read_text()
    nb=load(ROOT/'notebooks/23_Uji_Penerimaan_Akhir_SLR09_v0.8.1_executed.ipynb')
    assert nb['metadata']['execution_succeeded'] is False
    assert any(o.get('output_type')=='error' for c in nb['cells'] if c['cell_type']=='code' for o in c['outputs'])
    for name in ['24_Verifikasi_Perbaikan_Field_v0.8.2_executed.ipynb','24b_Verifikasi_Komposisi_Predikat_v0.8.2_executed.ipynb']:
        nb=load(ROOT/'notebooks'/name);assert nb['metadata']['execution_succeeded'] is True
        assert nb['metadata']['execution_engine']=='CPYTHON_CELL_EXECUTOR_ACTUAL_EXECUTION_NOT_NATIVE_JUPYTER_KERNEL'
    nb=load(ROOT/'notebooks/25_Uji_Penerimaan_SLR09_v0.8.2.ipynb')
    for c in nb['cells']:
        if c['cell_type']=='code':assert c['execution_count'] is None and c['outputs']==[];compile(''.join(c['source']),'notebook25','exec')
    current=load(ROOT/'acceptance/review_bundle_draft.json')
    assert all(sha(ROOT/p)==h for p,h in current['protocol']['binding']['files_sha256'].items())
    assert current['records']==proposals['records']
    result={'status':'SUCCEEDED','review_bintang_source_unchanged':True,'original50_gold_and_neural_predictions_preserved':True,
        'original_workflow_failure_preserved':True,'raw_sena_nara_outputs_unchanged_after_replay':True,
        'initial_nonempty_exact':[163,207],'final_regression_nonempty_exact':[177,207],
        'report_narratives':50,'new_reference_records':50,'new_reference_tokens':671,
        'new_reference_all_pending':True,'new_reference_reviewer_blank':True,'fake_approvals_saved':False,
        'blank_reviewer_rejected_before_inference':True,'completed_in_memory_fixture_validates':True,
        'new_candidate_binding_verified':True,'formula_errors':0,'notebook25_not_executed':True,
        'new_reference_inference_executed':False,'quality_acceptance_approved':False,'card_done':False}
    (ROOT/'evidence/field_fix_v082/artifact_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    verify(p.parse_args().output)
