"""New synthetic proposals, frozen before final-model evaluation. No inference."""
import json,re,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'code/acceptance'))
from evaluate_acceptance import token_items,validate_fields,ROLES,normal,write
out=ROOT/'data/final_reference_proposals_v0.8.1.json'
if out.exists():raise ValueError('Do not overwrite a frozen reference')
records=[]
def add(key,label,family,marked,location=None,time=None,parties=None,impacts=None,victims=None,objects=None):
 text='';spans=[];at=0
 for m in re.finditer(r'\{([A-Z-]+):([^}]+)\}',marked):
  text+=marked[at:m.start()];start=len(text);text+=m[2];spans.append((start,len(text),m[1]));at=m.end()
 text+=marked[at:];labels=[]
 for t in token_items(text):labels.append(next((role for a,b,role in spans if a<=t.start() and t.end()<=b),'O'))
 assert set(labels)<=set(ROLES)
 fields={'location_text':location,'time_text':time,'occurred_at':None,'involved_parties':parties or [],'impacts':impacts or [],'victims':victims or [],'affected_objects':objects or []};validate_fields(fields,text)
 records.append({'id':key,'text':text,'family':family,'gold_label':label,'gold_fields':fields,'gold_nara_labels':labels,'origin':{'kind':'ASSISTANT_AUTHORED_SYNTHETIC','reference':'v0.8.1 proposal, not a model prediction'},'review':{'status':'PENDING','reviewer':'','at':'','note':''}})
def tag(role,text):return '{'+role+':'+text+'}'
places=['Desa Rimbakencana','Kelurahan Banyumadu','Kampung Tirtajaya','Desa Cempakawana','Kelurahan Sumberasri','Jalan Lembayung','Kampung Wanasetra','Desa Beringinwangi','Kelurahan Kartasena','Kampung Harumjaya']
times=['subuh tadi','pagi ini','tadi malam','siang tadi','sore ini','pukul sembilan','malam ini','pagi tadi','sore tadi','kemarin sore']
classes=[('FLOOD','Banjir','menggenangi','tiga rumah','hujan deras'),('EARTHQUAKE','Gempa','merusak','dinding sekolah','pergeseran sesar'),('FIRE','Kebakaran','menghanguskan','satu warung','korsleting listrik'),('ACCIDENT','Kecelakaan','merusak','dua sepeda motor','rem blong')]
for label,event,verb,obj,reason in classes:
 for i in range(10):
  location=places[i]+' '+{'FLOOD':'Utara','EARTHQUAKE':'Selatan','FIRE':'Barat','ACCIDENT':'Tengah'}[label];tm=times[i];ev=tag(label+'-EVENT',event);loc=tag('STREET-ARG' if i==5 else 'PLACE-ARG',location);tt=tag('TIME-ARG',tm);action=tag('INFORMATION-ARG',verb)+' '+tag('AFFECTEDOBJECTS-ARG',obj);parties=[];victims=[];family='plain'
  if i==0:text=f'Menurut warga, {ev} {action} di {loc} {tt}.'
  elif i==1:
   v='dua warga luka ringan';victims=[v];text=f'{ev} {action} di {loc} {tt}; '+tag('WOUNDVICTIM-ARG',v)+'.'
  elif i==2:
   v='seorang penjaga meninggal';victims=[v];text=f'{ev} {action} di {loc} {tt}; '+tag('DEATHVICTIM-ARG',v)+'.'
  elif i==3:text=f'{ev} dipicu '+tag('REASON-ARG',reason)+f' di {loc} {tt} dan {action}.';family='cause'
  elif i==4:parties=['Petugas BPBD'];text=tag('OFFICER-ARG','Petugas BPBD')+f' tiba di {loc} {tt} setelah {ev} {action}.'
  elif i==5:text=f'{ev} di {loc} {tt} {action}; jalur tersebut sekarang ditutup.';family='street'
  elif i==6:parties=['petugas'];text=f'{ev} {action} di {loc} {tt}; '+tag('OFFICER-ARG','petugas')+' memastikan tidak ada korban.';family='local_negation'
  elif i==7:text=f'Di tengah latihan evakuasi, {ev} sungguhan {action} di {loc} {tt}.';family='real_during_exercise'
  elif i==8:text=f'Bukan sekadar kabar: {ev} benar-benar {action} di {loc} {tt}.';family='rumor_verified'
  else:text=f'Rekaman ini bukan adegan film. {ev} {action} di {loc} {tt}.';family='fiction_denied'
  add(f'FINAL081-{label}-{i+1:02d}',label,family,text,location,tm,parties,[verb+' '+obj],victims,[obj])
add('FINAL081-NON_EVENT-01','NON_EVENT','simulation',tag('OFFICER-ARG','Petugas BPBD')+' menggelar simulasi '+tag('FALSE-EVENT','kebakaran')+' di '+tag('PLACE-ARG','lapangan Kalimurni')+' '+tag('TIME-ARG','sore ini')+'.','lapangan Kalimurni','sore ini',['Petugas BPBD'])
add('FINAL081-NON_EVENT-02','NON_EVENT','exercise_only','Latihan penanganan '+tag('FALSE-EVENT','kecelakaan')+' diselenggarakan di '+tag('PLACE-ARG','balai pelatihan Puspasari')+' '+tag('TIME-ARG','pagi ini')+'.','balai pelatihan Puspasari','pagi ini')
add('FINAL081-NON_EVENT-03','NON_EVENT','forecast',tag('TIME-ARG','Besok')+' ada prakiraan potensi '+tag('FALSE-EVENT','banjir')+' di '+tag('PLACE-ARG','Kelurahan Cendana Baru')+'.','Kelurahan Cendana Baru','Besok')
add('FINAL081-NON_EVENT-04','NON_EVENT','denial',tag('OFFICER-ARG','Petugas')+' memastikan tidak terjadi '+tag('FALSE-EVENT','gempa')+' di '+tag('PLACE-ARG','Desa Lazuardi')+' '+tag('TIME-ARG','siang tadi')+'.','Desa Lazuardi','siang tadi',['Petugas'])
add('FINAL081-NON_EVENT-05','NON_EVENT','metaphor','Unggahan toko itu menulis '+tag('FALSE-EVENT','banjir')+' pesanan sejak '+tag('TIME-ARG','pagi tadi')+'.',time='pagi tadi')
add('FINAL081-NON_EVENT-06','NON_EVENT','prevention',tag('OFFICER-ARG','Tim kelurahan')+' menyiapkan jalur evakuasi untuk mengantisipasi '+tag('FALSE-EVENT','banjir')+' di '+tag('PLACE-ARG','Kampung Manggala')+'.','Kampung Manggala',parties=['Tim kelurahan'])
add('FINAL081-NON_EVENT-07','NON_EVENT','education','Buku keselamatan menjelaskan cara menghindari '+tag('FALSE-EVENT','kebakaran')+' akibat kompor bocor.')
add('FINAL081-NON_EVENT-08','NON_EVENT','statistics','Artikel itu membahas sepuluh '+tag('FALSE-EVENT','kecelakaan')+' terburuk sepanjang dekade, tanpa laporan kejadian tertentu.')
add('FINAL081-NON_EVENT-09','NON_EVENT','donation_aggregate','Panitia membuka donasi tahunan untuk para penyintas '+tag('FALSE-EVENT','gempa')+' dan '+tag('FALSE-EVENT','banjir')+' dari beberapa tahun berbeda.')
add('FINAL081-NON_EVENT-10','NON_EVENT','fiction','Di panggung teater, para pemain memeragakan '+tag('FALSE-EVENT','gempa')+' menggunakan efek suara; penonton tetap duduk.')
known=set()
def collect(x):
 if isinstance(x,dict):
  if isinstance(x.get('text'),str):known.add(normal(x['text']))
  for v in x.values():collect(v)
 elif isinstance(x,list):
  for v in x:collect(v)
for folder in ('data','evidence'):
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and p.suffix in ('.json','.jsonl'):
   if p.suffix=='.json':collect(json.loads(p.read_text()))
   else:
    for line in p.read_text().splitlines():
     if line.strip():collect(json.loads(line))
assert len(records)==50 and len({normal(r['text']) for r in records})==50
assert not known&{normal(r['text']) for r in records}
roles=Counter(l for r in records for l in r['gold_nara_labels']);assert set(roles)==set(ROLES)
write(out,{'schema':'slr09-final-proposals-0.8.1','created_at':datetime.now(timezone.utc).isoformat(),'human_reference_review_completed':False,'model_inference_executed':False,'development39_approval_does_not_approve_these50':True,'records':records})
write(ROOT/'data/final_reference_identity_v0.8.1.json',{'records':50,'tokens':sum(roles.values()),'role_support':roles,'class_support':Counter(r['gold_label'] for r in records),'normalized_exact_overlap_available_sources':0,'semantic_independence_established':False,'population_representativeness_established':False,'human_reference_review_completed':False,'model_inference_executed':False,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
print(json.dumps({'new_reference_records':50,'tokens':sum(roles.values()),'status':'PENDING','model_inference_executed':False}))
