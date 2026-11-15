import test from 'node:test';
import assert from 'node:assert/strict';
let version=0;
async function client(fetcher){
  Object.defineProperty(globalThis,'navigator',{configurable:true,value:{onLine:true}});
  globalThis.fetch=fetcher;
  return import(`../src/session.js?test=${++version}`);
}
const json=data=>new Response(JSON.stringify(data),{status:200});
const actor={id:'qa-user',role:'REPORTER',full_name:'Pelapor Uji'};

test('Pemulihan sesi berbagi satu refresh, membaca akun, dan tidak mengulang pada navigasi berikutnya',async()=>{
  const calls=[];
  const {session,restoreSession}=await client(async(path,options)=>{
    calls.push(path);
    if(path.endsWith('csrf/'))return json({data:{csrf_token:'qa-csrf'}});
    if(path.endsWith('refresh/')){assert.equal(options.method,'POST');return json({data:{access:'qa-access'}});}
    assert.equal(options.headers.Authorization,'Bearer qa-access');return json({data:actor});
  });
  await Promise.all([restoreSession(),restoreSession(),restoreSession()]);
  assert.equal(session.ready,true);assert.equal(session.user.id,actor.id);assert.equal(session.restoreError,null);
  assert.equal(calls.length,3);await restoreSession();assert.equal(calls.length,3);
});

test('Sesi kedaluwarsa menjadi anonim tanpa retry refresh otomatis',async()=>{
  const calls=[];
  const {session,restoreSession}=await client(async path=>{
    calls.push(path);
    return path.endsWith('csrf/')?json({data:{csrf_token:'qa-csrf'}}):new Response(JSON.stringify({error:{code:'TOKEN_EXPIRED',message:'Expired'}}),{status:401});
  });
  await restoreSession();assert.equal(session.user,null);assert.equal(session.ready,true);assert.equal(session.restoreError,null);
  await restoreSession();assert.equal(calls.length,2);
});

test('Penolakan akun sesudah refresh baru tidak memulai refresh kedua atau melewati tenggat awal',async()=>{
  const calls=[];
  const {session,restoreSession}=await client(async path=>{
    calls.push(path);
    if(path.endsWith('csrf/'))return json({data:{csrf_token:'qa-csrf'}});
    if(path.endsWith('refresh/'))return json({data:{access:'qa-access'}});
    return new Response(JSON.stringify({error:{code:'AUTHENTICATION_FAILED',message:'Akun tidak tersedia.'}}),{status:401});
  });
  await restoreSession();assert.equal(session.user,null);assert.equal(session.ready,true);
  assert.equal(calls.length,3);assert.equal(calls.filter(path=>path.endsWith('refresh/')).length,1);
});

test('Gangguan koneksi tidak dianggap logout: pemeriksaan eksplisit dapat memulihkan cookie yang masih valid',async()=>{
  let connected=false;let refreshes=0;
  const {session,restoreSession}=await client(async path=>{
    if(!connected)throw new TypeError('connection lost');
    if(path.endsWith('csrf/'))return json({data:{csrf_token:'qa-csrf'}});
    if(path.endsWith('refresh/')){refreshes++;return json({data:{access:'qa-access'}});}
    return json({data:actor});
  });
  await restoreSession();assert.equal(session.user,null);assert(session.restoreError);assert.equal(session.ready,true);
  connected=true;await restoreSession({retry:true});assert.equal(session.user.id,actor.id);assert.equal(session.restoreError,null);assert.equal(session.message,'');assert.equal(refreshes,1);
});

test('Logout eksplisit menghapus akun dan tidak memulihkannya lagi saat kembali ke halaman publik',async()=>{
  let refreshes=0;
  const {session,restoreSession,signOut}=await client(async path=>{
    if(path.endsWith('csrf/'))return json({data:{csrf_token:'qa-csrf'}});
    if(path.endsWith('refresh/')){refreshes++;return json({data:{access:'qa-access'}});}
    if(path.endsWith('logout/'))return new Response(null,{status:204});
    return json({data:actor});
  });
  await restoreSession();await signOut();await restoreSession();
  assert.equal(session.user,null);assert.equal(session.restoreError,null);assert.equal(refreshes,1);
});
