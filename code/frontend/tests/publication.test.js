import test from 'node:test';
import assert from 'node:assert/strict';
import { publicListPath, publicProjection, publicValue } from '../src/publication.js';
import { decisionAllowed } from '../src/workspace.js';

test('Public pagination retains both filters and requests exactly ten cards',()=>{
  const path=publicListPath({q:'  Jalan & sungai  ',category:'FLOOD',page:2});
  const query=new URL(path,'https://example.test/').searchParams;
  assert.equal(query.get('q'),'Jalan & sungai');
  assert.equal(query.get('event_type'),'FLOOD');
  assert.equal(query.get('page'),'2');assert.equal(query.get('page_size'),'10');
  assert.equal(query.has('ordering'),false);
});

test('Internal publication preview cannot project extra legacy fields or a version UUID',()=>{
  const version={id:'private-version',published_at:null,data:{event_type:'FLOOD',summary:'Ringkasan publik',owner:'private-owner',evidence:['secret'],victims:['private'],time_text:'Sore hari'}};
  const projected=publicProjection(version,'report-id');
  assert.equal(projected.id,'report-id');assert.equal(projected.summary,'Ringkasan publik');
  assert.equal(projected.occurred_at,null);assert.equal(publicValue(projected,'occurred_at'),'Belum tersedia');
  assert.deepEqual(Object.keys(projected).sort(),['id','event_type','summary','general_location','time_text','occurred_at','general_impact','handling_update','published_at'].sort());
});

test('Preparing a replacement preserves a published report, including after candidate cancellation',()=>{
  const detail={reviews:[{}],has_active_candidate:false,report:{publication_status:'PUBLISHED',validation_status:'VALID',published_version_id:'published-version'}};
  assert.equal(decisionAllowed(detail,'PREPARE'),true);
  assert.equal(decisionAllowed(detail,'INTERNAL'),false);
  assert.equal(decisionAllowed({...detail,has_active_candidate:true},'PREPARE'),false);
  assert.equal(decisionAllowed({...detail,report:{...detail.report,publication_status:'PENDING_APPROVAL'}},'INTERNAL'),false);
});

test('Public requests omit account credentials and do not refresh after an HTTP error',async()=>{
  Object.defineProperty(globalThis,'navigator',{configurable:true,value:{onLine:true}});
  const calls=[];
  globalThis.fetch=async(path,options)=>{calls.push({path,options});return new Response(JSON.stringify({error:{code:'NOT_FOUND',message:'Tidak tersedia.'}}),{status:404});};
  const {publicRead}=await import('../src/api.js?publication-test');
  await assert.rejects(publicRead('public/reports/missing/'),error=>error.status===404);
  assert.equal(calls.length,1);assert.equal(calls[0].options.credentials,'omit');
  assert.equal(calls[0].options.cache,'no-store');assert.equal(calls[0].options.headers.Authorization,undefined);
  assert.throws(()=>publicRead('reports/private/'));
});
