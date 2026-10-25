import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiError } from '../src/api.js';
import { LIMITS } from '../src/domain.js';
import { defaultEvidence, useSavedEvidence, sameEvidence, uploadProblem, analyseSavedEvidence } from '../src/evidence.js';
const item=(id,type,day,byte_size=100)=>({id,type,created_at:`2026-10-${day}T00:00:00Z`,byte_size});
const first=item('t1','TEXT','20'),second=item('t2','TEXT','22'),audio=item('a1','AUDIO','20'),image=item('i1','IMAGE','20');
const bundle={id:'bundle-old',report_id:'r',created_at:'2026-10-21T00:00:00Z',items:[first,audio].map(evidence=>({evidence}))};
const detail={report:{id:'r',revision:4,input_revision:1},active_bundle:null};

test('Keterangan terbaru menjadi aktif sebelum bundle; semua gambar dan satu audio ikut otomatis',()=>{
  const rows=[second,audio,first,image];
  const selected=defaultEvidence(rows,null);
  assert.deepEqual(new Set(selected.map(x=>x.id)),new Set(['t2','a1','i1']));
  assert.equal(rows.length,4);assert.equal(first.id,'t1');
});
test('Bundle aktif mempertahankan pilihan sumber lama; hanya unggahan sesudahnya yang mengganti kanal',()=>{
  assert.deepEqual(new Set(defaultEvidence([first,audio,image],bundle).map(x=>x.id)),new Set(['t1','a1']));
  assert.deepEqual(new Set(defaultEvidence([first,audio,second],bundle).map(x=>x.id)),new Set(['t2','a1']));
});
test('Penggantian keterangan/audio mempertahankan gambar dan tidak menyertakan dua item kanal yang sama',()=>{
  const selected=useSavedEvidence([first,image,audio],second);
  assert.deepEqual(selected.map(x=>x.id),['i1','a1','t2']);
  assert.deepEqual(useSavedEvidence(selected,{...audio,id:'a2'}).map(x=>x.id),['i1','t2','a2']);
});
test('Riwayat gambar lebih dari tiga tidak dipangkas diam-diam',()=>{
  const rows=Array.from({length:4},(_,i)=>item('i'+i,'IMAGE','20'));
  assert.equal(defaultEvidence(rows,null).length,4);
  assert.ok(uploadProblem(defaultEvidence(rows,null),'TEXT',['kejadian']));
});
test('Batas gambar dan total byte diperiksa sebelum kelompok unggahan dikirim',()=>{
  const selected=[image,item('i2','IMAGE','20')];
  assert.equal(uploadProblem(selected,'IMAGE',[{size:100}]),'');
  assert.ok(uploadProblem(selected,'IMAGE',[{size:100},{size:100}]));
  assert.ok(uploadProblem([{...audio,byte_size:LIMITS.bundle-1}],'TEXT',['🌧']));
  assert.equal(uploadProblem([first],'TEXT',['teks revisi']),'');
});
test('Pemeriksaan sumber sama mengabaikan urutan tetapi menolak ID duplikat',()=>{
  assert.equal(sameEvidence(bundle.items,['a1','t1']),true);
  assert.equal(sameEvidence(bundle.items,['t1','t1']),false);
});
test('Analisis satu klik menyimpan snapshot dahulu dan memakai revision hasil commit',async()=>{
  const calls=[];let prepared;
  await analyseSavedEvidence(async(path,options)=>{
    calls.push({path,...options});
    if(path.endsWith('/bundles/'))return {data:{report:{id:'r',revision:5,input_revision:2},object:{id:'b',report_id:'r',items:[{evidence:first}]}}};
    return {data:{}};
  },detail,[first],false,value=>prepared=value);
  assert.deepEqual(calls.map(x=>x.path),['reports/r/bundles/','reports/r/analyses/']);
  assert.deepEqual(calls[0].body,{evidence_ids:['t1'],expected_revision:4});
  assert.deepEqual(calls[1].body,{mode:'EVIDENCE',bundle_id:'b',input_revision:2,expected_revision:5});
  assert.notEqual(calls[0].key,calls[1].key);
  assert.equal(prepared.current_card,null);assert.equal(prepared.active_bundle.id,'b');
});
test('Sumber tidak berubah memakai bundle aktif tanpa membentuk versi baru',async()=>{
  const calls=[];
  await analyseSavedEvidence(async(path,options)=>calls.push({path,...options}),{...detail,active_bundle:bundle},[audio,first],true);
  assert.equal(calls.length,1);assert.equal(calls[0].path,'reports/r/analyses/');assert.equal(calls[0].body.bundle_id,bundle.id);
});
test('Informasi Gemini diperiksa sebelum persiapan sumber atau analisis',async()=>{
  let calls=0;
  await assert.rejects(analyseSavedEvidence(async()=>calls++,detail,[image],false),error=>error.code==='INVALID_PAYLOAD');
  assert.equal(calls,0);
});
test('Respons persiapan terputus menahan analisis dan tidak mengulang POST',async()=>{
  const calls=[];
  await assert.rejects(analyseSavedEvidence(async(path)=>{calls.push(path);throw new ApiError('terputus','RESPONSE_UNKNOWN');},detail,[first],false),error=>error.code==='RESPONSE_UNKNOWN');
  assert.deepEqual(calls,['reports/r/bundles/']);
});
test('Sumber pada respons persiapan yang tidak sesuai tidak diteruskan ke analisis',async()=>{
  const calls=[];
  await assert.rejects(analyseSavedEvidence(async(path)=>{calls.push(path);return {data:{report:{id:'r'},object:{id:'b',report_id:'r',items:[{evidence:second}]}}};},detail,[first],false),error=>error.code==='RESPONSE_UNKNOWN');
  assert.equal(calls.length,1);
});
test('Kegagalan analisis setelah snapshot tersimpan mempertahankan snapshot untuk pemulihan',async()=>{
  const calls=[];let prepared;
  await assert.rejects(analyseSavedEvidence(async(path)=>{calls.push(path);if(path.endsWith('/analyses/'))throw new ApiError('provider belum siap','AI_CONFIGURATION_NOT_READY',503);return {data:{report:{id:'r',revision:5,input_revision:2},object:{id:'b',report_id:'r',items:[{evidence:first}]}}};},detail,[first],false,value=>prepared=value),error=>error.code==='AI_CONFIGURATION_NOT_READY');
  assert.equal(calls.length,2);assert.equal(prepared.active_bundle.id,'b');
});
