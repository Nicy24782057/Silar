import test from 'node:test';import assert from 'node:assert/strict';import vm from 'node:vm';
import { makeServiceWorker } from '../tools/service-worker.js';
function worker(){const events={};const writes=[];const self={location:{origin:'https://silar.test'},clients:{claim:async()=>{}},addEventListener:(key,fn)=>events[key]=fn};const caches={keys:async()=>[],delete:async()=>{},open:async()=>({addAll:async assets=>writes.push(...assets),match:async()=>new Response('UI'),put:async key=>writes.push(key)})};vm.runInNewContext(makeServiceWorker(['/index.html','/assets/app.js'],'test'),{self,caches,URL,fetch:async()=>new Response('UI')});return{events,writes};}
test('Precache hanya daftar aset antarmuka',async()=>{const {events,writes}=worker();let work;events.install({waitUntil:promise=>work=promise});await work;assert.deepEqual(writes,['/index.html','/assets/app.js']);});
test('Auth, API privat, media, POST dan origin lain tidak diintersep',()=>{const {events}=worker();for(const [url,method]of[['https://silar.test/api/v1/auth/login/','POST'],['https://silar.test/api/v1/reports/','GET'],['https://silar.test/api/v1/evidence/id/media/','GET'],['https://other.test/assets/app.js','GET']]){let intercepted=false;events.fetch({request:{url,method,mode:'cors'},respondWith:()=>intercepted=true});assert.equal(intercepted,false);}});
test('Aktivasi pembaruan menghapus cache aset SILAR lama dan mempertahankan cache aktif serta aplikasi lain',async()=>{
  const events={},deleted=[];
  const self={clients:{claim:async()=>{}},addEventListener:(name,callback)=>events[name]=callback};
  const caches={keys:async()=>['silar-ui-before','silar-ui-current','other-app'],delete:async key=>deleted.push(key)};
  vm.runInNewContext(makeServiceWorker(['/index.html'],'current'),{self,caches});
  let work;events.activate({waitUntil:value=>work=value});await work;
  assert.deepEqual(deleted,['silar-ui-before']);
});
