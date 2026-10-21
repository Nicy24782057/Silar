"""Baca tabel review Excel tanpa macro/dependency tambahan; validasi sebelum inferensi."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET

from evaluate_acceptance import ROOT, FIELDS, ROLES, LABELS, token_items, validate, write

NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
PKG = '{http://schemas.openxmlformats.org/package/2006/relationships}'


def read_cells(path):
    with zipfile.ZipFile(path) as archive:
        if sum(x.file_size for x in archive.infolist()) > 30_000_000:
            raise ValueError('Ukuran isi workbook tidak sesuai kit review')
        strings=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared=ET.fromstring(archive.read('xl/sharedStrings.xml'))
            strings=[''.join(t.text or '' for t in item.findall('.//s:t',NS)) for item in shared]
        rels=ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        links={x.attrib['Id']:x.attrib['Target'] for x in rels if x.attrib.get('TargetMode')!='External'}
        result={}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet',NS):
            target=links[sheet.attrib[REL]]
            target=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join('xl',target))
            if not target.startswith('xl/') or '..' in target.split('/'):
                raise ValueError('Lokasi worksheet tidak valid')
            cells={}
            for c in ET.fromstring(archive.read(target)).findall('.//s:sheetData/s:row/s:c',NS):
                value=c.find('s:v',NS)
                if c.attrib.get('t')=='s':
                    text=strings[int(value.text)] if value is not None else ''
                elif c.attrib.get('t')=='inlineStr':
                    text=''.join(t.text or '' for t in c.findall('.//s:t',NS))
                else:
                    text=value.text if value is not None and value.text is not None else ''
                cells[c.attrib['r']]=(text,c.find('s:f',NS) is not None)
            result[sheet.attrib['name']]=cells
        return result


def value(cells,address):
    text,formula=cells.get(address,('',False))
    if formula:
        raise ValueError('Input review harus nilai biasa, bukan formula: '+address)
    return text.strip()


def read_table(cells,expected):
    actual=[value(cells,f'{chr(65+i)}5') for i in range(len(expected))]
    if actual!=expected:
        raise ValueError('Header baris 5 berubah: '+str(actual))
    rows=[]
    row_numbers=sorted({int(re.sub('[A-Z]','',a)) for a in cells if int(re.sub('[A-Z]','',a))>=6})
    for number in row_numbers:
        values=[value(cells,f'{chr(65+i)}{number}') for i in range(len(expected))]
        if not any(values):continue
        rows.append(dict(zip(expected,values)))
    return rows


def convert(path, output=None, root=ROOT, validate_ready=True):
    sheets=read_cells(path)
    if not {'Mulai','Narasi','Token'}<=set(sheets):
        raise ValueError('Gunakan workbook review yang disediakan: Mulai, Narasi, Token')
    bundle=json.loads((root/'acceptance/review_bundle_draft.json').read_text())
    reviewer=value(sheets['Mulai'],'B5')
    if not reviewer:
        raise ValueError('Isi nama reviewer pada Mulai!B5')
    # Persetujuan target berasal dari pesan eksplisit pemilik, bukan status review label.
    if value(sheets['Mulai'],'B6')!='DISETUJUI_PEMILIK':
        raise ValueError('Catatan persetujuan target berubah')
    keys=list(bundle['protocol']['targets'])
    for i,key in enumerate(keys,19):
        if value(sheets['Mulai'],f'A{i}')!=key:
            raise ValueError('ID metrik berubah pada tabel target')
        if float(value(sheets['Mulai'],f'B{i}'))!=bundle['protocol']['targets'][key]:
            raise ValueError('Target yang sudah disetujui berubah; catat keputusan baru sebelum pengujian')
    rows=read_table(sheets['Narasi'],['ID','Narasi','Kategori','Lokasi','Waktu','Pihak','Dampak','Korban','Objek','Status','Catatan'])
    tokens=read_table(sheets['Token'],['ID','Posisi','Token','Label'])
    if len(rows)!=len(bundle['records']) or len({x['ID'] for x in rows})!=len(rows):
        raise ValueError('Jumlah/ID narasi kurang atau duplikat')
    row_by_id={r['ID']:r for r in rows}
    expected_ids={r['id'] for r in bundle['records']}
    if set(row_by_id)!=expected_ids:
        raise ValueError('ID narasi berbeda dari kit')
    token_by_id={key:{} for key in expected_ids}
    for item in tokens:
        key=item['ID']
        if key not in token_by_id or not item['Posisi'].isdigit():
            raise ValueError('ID/posisi token tidak valid')
        pos=int(item['Posisi'])
        if pos in token_by_id[key]:
            raise ValueError('Posisi token duplikat: '+key)
        token_by_id[key][pos]=item
    at=datetime.now(timezone.utc).isoformat()
    for original in bundle['records']:
        key=original['id'];row=row_by_id[key]
        if row['Narasi']!=original['text']:
            raise ValueError('Teks narasi berubah; kit ini hanya mengedit acuan: '+key)
        if row['Kategori'] not in LABELS or row['Status'] not in {'PENDING','APPROVED','DEFERRED'}:
            raise ValueError('Kategori/status tidak valid: '+key)
        expected_tokens=token_items(original['text'])
        indexed=token_by_id[key]
        if set(indexed)!=set(range(1,len(expected_tokens)+1)):
            raise ValueError('Posisi token kurang/berlebih: '+key)
        labels=[]
        for pos,match in enumerate(expected_tokens,1):
            item=indexed[pos]
            if item['Token']!=match.group() or item['Label'] not in ROLES:
                raise ValueError('Token/label tidak valid: '+key+' posisi '+str(pos))
            labels.append(item['Label'])
        def items(column):
            return [x.strip() for x in row[column].split('|') if x.strip()]
        original['gold_label']=row['Kategori']
        original['gold_fields']={'location_text':row['Lokasi'] or None,'time_text':row['Waktu'] or None,'occurred_at':None,
            'involved_parties':items('Pihak'),'impacts':items('Dampak'),'victims':items('Korban'),'affected_objects':items('Objek')}
        original['gold_nara_labels']=labels
        original['review']={'status':row['Status'],'reviewer':reviewer if row['Status']!='PENDING' else '',
                            'at':at if row['Status']!='PENDING' else '', 'note':row['Catatan']}
    bundle['excel_import']={'source_name':Path(path).name,'imported_at':at,
        'reviewer_from':'Mulai!B5','review_time_basis':'Import timestamp after user-set row statuses; not an asserted Excel edit timestamp'}
    if validate_ready:validate(bundle,root)
    if output is not None:write(output,bundle)
    return bundle
