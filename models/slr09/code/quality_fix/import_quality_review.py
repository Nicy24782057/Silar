"""Import reviewed class labels for further development, never grant acceptance."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/acceptance'))
from import_review_xlsx import read_cells, read_table, value
from evaluate_acceptance import person, LABELS, write


def convert(path, output=None):
    source=json.loads((ROOT/'data/quality_fix_review_items_v0.5.json').read_text())
    sheets=read_cells(path)
    if 'Review Data' not in sheets:raise ValueError('Tab Review Data tidak ditemukan')
    sheet=sheets['Review Data'];reviewer=value(sheet,'B4')
    if not person(reviewer):raise ValueError('Isi nama reviewer pada Review Data!B4')
    table=read_table(sheet,['ID','Narasi','Label sumber','Kelas reviewer','Status','Catatan','Asal label'])
    by_id={r['ID']:r for r in table}
    if len(table)!=len(by_id) or set(by_id)!={r['id'] for r in source['records']}:
        raise ValueError('ID/jumlah baris review berubah')
    approved=[];excluded=[];pending=[]
    at=datetime.now(timezone.utc).isoformat()
    for original in source['records']:
        row=by_id[original['id']]
        if row['Narasi']!=original['text'] or row['Label sumber']!=original['gold_label'] or row['Asal label']!=original['origin']:
            raise ValueError('Teks/label/asal sumber diubah; koreksi kelas di Kelas reviewer: '+original['id'])
        status=row['Status']
        if status=='PENDING':pending.append(original['id']);continue
        if status=='DEFERRED':
            if not row['Catatan']:raise ValueError('DEFERRED perlu catatan: '+original['id'])
            excluded.append({'id':original['id'],'note':row['Catatan']});continue
        if status!='APPROVED' or row['Kelas reviewer'] not in LABELS:
            raise ValueError('Pilih kelas reviewer dan status yang valid: '+original['id'])
        approved.append({'id':original['id'],'text':original['text'],'final':row['Kelas reviewer'],
                         'source_label':original['gold_label'],'origin':original['origin'],
                         'review':{'status':'APPROVED','reviewer':reviewer,'at':at,'note':row['Catatan']}})
    if not approved:raise ValueError('Belum ada label yang disetujui; tidak ada data training diekspor')
    result={'schema':'slr09-quality-class-review-0.5','records':approved,'deferred':excluded,'pending':pending,
            'source_workbook_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'imported_at':at,'training_executed':False,'model_inference_executed':False,
            'eligible_as_fresh_acceptance_data':False,'quality_acceptance_approved':False,
            'scope':'HUMAN_REVIEWED_DEVELOPMENT_LABELS_ON_ALREADY_SEEN_INPUTS'}
    if output is not None:write(output,result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workbook',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=convert(a.workbook,a.output);print('Label development disetujui:',len(result['records']))
