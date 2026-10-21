"""Check saved workbook values and pending-review guards without model inference."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch
import zipfile
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/acceptance'))
from import_review_xlsx import read_cells,convert,value,read_table
from evaluate_acceptance import validate,token_items


def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(output):
    kit=output/'Review_Penerimaan_Akhir_SLR09_v0.8.1.xlsx'
    report=output/'SLR09_Hasil_Perbaikan_v0.8.1.xlsx'
    source=ROOT/'results/quality_fix_v07/SLR09_Hasil_Perbaikan_v0.7.xlsx'
    cells=read_cells(kit);report_cells=read_cells(report);source_cells=read_cells(source)
    assert not value(cells['Mulai'],'B5')
    assert value(cells['Mulai'],'B6')=='DISETUJUI_PEMILIK'
    narratives=read_table(cells['Narasi'],['ID','Narasi','Kategori','Lokasi','Waktu','Pihak','Dampak','Korban','Objek','Status','Catatan'])
    tokens=read_table(cells['Token'],['ID','Posisi','Token','Label'])
    proposals=load(ROOT/'data/final_reference_proposals_v0.8.1.json')
    assert len(narratives)==50 and Counter(r['Status'] for r in narratives)=={'PENDING':50}
    assert len(tokens)==762
    by_id={r['id']:r for r in proposals['records']}
    expected=[]
    for row in narratives:
        original=by_id[row['ID']]
        assert row['Narasi']==original['text'] and row['Kategori']==original['gold_label']
        for pos,(token,label) in enumerate(zip(token_items(original['text']),original['gold_nara_labels']),1):
            expected.append({'ID':row['ID'],'Posisi':str(pos),'Token':token.group(),'Label':label})
    assert tokens==expected
    pending_error=None
    try:convert(kit,root=ROOT)
    except ValueError as error:pending_error=str(error)
    assert pending_error=='Isi nama reviewer pada Mulai!B5'
    # Only change an in-memory read result; no reviewed workbook is created.
    memory={name:dict(rows) for name,rows in cells.items()}
    memory['Mulai']['B5']=('FIXTURE ONLY',False)
    with patch('import_review_xlsx.read_cells',return_value=memory):
        try:convert(kit,root=ROOT)
        except ValueError as error:assert 'belum direview' in str(error)
        else:raise AssertionError('PENDING reference was accepted')
    for i in range(6,46):
        for column in ('A','B','C','G'):
            assert source_cells['Review Data'].get(f'{column}{i}')==report_cells['Review Data'].get(f'{column}{i}')
    original_fields={k:v for k,v in source_cells['Perubahan Field'].items() if v[0]}
    new_fields={k:v for k,v in report_cells['Perubahan Field'].items() if v[0]}
    assert original_fields==new_fields
    approval=load(ROOT/'data/development_review_v0.8.json')
    approved={r['id']:r for r in approval['records']}
    statuses=[]
    for i in range(6,46):
        c=report_cells['Review Data'];key=value(c,f'A{i}');reference=approved[key]
        assert value(c,f'D{i}')==(reference['final'] or '')
        assert value(c,f'E{i}')==reference['review']['status']
        assert reference['review']['at'] in value(c,f'F{i}')
        statuses.append(reference['review']['status'])
    assert Counter(statuses)=={'APPROVED':39,'DEFERRED':1}
    for p in (kit,report):
        with zipfile.ZipFile(p) as archive:
            assert archive.testzip() is None
            if p==kit:
                ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                sheets=[ET.fromstring(archive.read(f'xl/worksheets/sheet{i}.xml')) for i in (2,3)]
                assert all(s.find('.//s:pane',ns) is not None for s in sheets)
                assert len(sheets[0].findall('.//s:dataValidation',ns))>=2
                assert len(sheets[1].findall('.//s:dataValidation',ns))>=1
                assert all(s.find('.//s:tablePart',ns) is not None for s in sheets)
        scan=output/(p.stem+'_formula_scan.ndjson')
        assert 'Cell search matched 0 entries.' in scan.read_text()
        assert not any(v[0].startswith(('#REF!','#DIV/0!','#VALUE!','#NAME?','#SPILL!')) for sheet in read_cells(p).values() for v in sheet.values())
    for number in (20,21,22,'22b'):
        paths=list((ROOT/'notebooks').glob(f'{number}_*v0.8.1_executed.ipynb'));assert len(paths)==1
        notebook=load(paths[0]);assert notebook['metadata']['execution_succeeded'] is True
        assert notebook['metadata']['execution_engine']=='CPYTHON_CELL_EXECUTOR_ACTUAL_EXECUTION_NOT_NATIVE_JUPYTER_KERNEL'
        assert all(c.get('execution_count') is not None and not any(o.get('output_type')=='error' for o in c['outputs'])
                   for c in notebook['cells'] if c['cell_type']=='code')
    notebook=load(ROOT/'notebooks/23_Uji_Penerimaan_Akhir_SLR09_v0.8.1.ipynb')
    for c in notebook['cells']:
        if c['cell_type']=='code':
            assert c['execution_count'] is None and c['outputs']==[]
            compile(''.join(c['source']),'notebook23','exec')
    bundle=load(ROOT/'acceptance/review_bundle_draft.json')
    assert bundle['records']==proposals['records']
    assert all(sha(ROOT/path)==expected for path,expected in bundle['protocol']['binding']['files_sha256'].items())
    result={'status':'SUCCEEDED','saved_excel_rows':50,'saved_excel_tokens':762,
        'new_reference_all_pending':True,'reviewer_blank':True,'fake_approvals_saved':False,
        'unreviewed_workbook_rejected_before_model_load':True,'rejection':pending_error,
        'source40_preserved':True,'source_field_detail_preserved':True,
        'approved_development':39,'deferred_development':1,
        'native_validation_tables_freeze_panes_present':True,'formula_errors':0,
        'notebooks20_21_22_22b_actual_cpython_success':True,'notebook23_not_executed':True,
        'candidate_binding_verified':True,'model_inference_executed_by_this_check':False,
        'quality_acceptance_approved':False,'card_done':False}
    p=ROOT/'evidence/quality_fix_v081/review_artifact_verification.json'
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    verify(p.parse_args().output)
