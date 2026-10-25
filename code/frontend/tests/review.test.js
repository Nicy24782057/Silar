import test from 'node:test';
import assert from 'node:assert/strict';
import {cardForm, correctionPatch, reviewState} from '../src/review.js';
import {readStoredReportAction, reportRequestGuidance, reportRequests} from '../src/recovery.js';

function detail(){
  const narrative={id:'n',bundle_id:'b',text:'Air menggenangi jalan.'};
  return {report:{id:'r',revision:5,input_revision:2,workflow_status:'NOT_SUBMITTED',preparation_status:'AWAITING_CONFIRMATION',
      current_card_version_id:'c',active_bundle_id:'b',active_narrative_id:'n'},
    current_card:{id:'c',bundle_id:'b',narrative_id:'n',sena_result_id:'s',nara_result_id:'a',uncertain:true,data:{event_type:'FLOOD'}},
    active_narrative:narrative,verification:null,
    latest_run:{id:'run',status:'SUCCEEDED',bundle_id:'b',input_revision:2,output_narrative_id:'n',output_narrative:narrative,
      sena:{id:'s',analysis_run_id:'run',narrative_id:'n',category:'FLOOD'},nara:{id:'a',analysis_run_id:'run',narrative_id:'n'}}};
}

test('Uncertain with missing incident fields can be confirmed; submission needs verification of the exact card',()=>{
  const value=detail();
  assert.equal(reviewState(value).canConfirm,true);
  assert.equal(reviewState(value).canSubmit,false);
  value.verification={card_version_id:'c'};value.report.preparation_status='READY';
  assert.equal(reviewState(value).canSubmit,true);
  value.verification.card_version_id='older';
  assert.equal(reviewState(value).canSubmit,false);
});

test('NON_EVENT, mismatched source/run and unknown execution never enable confirmation or submission',()=>{
  for(const change of [v=>v.latest_run.sena.category='NON_EVENT',v=>v.current_card.data.event_type=null,
    v=>v.latest_run.status='UNKNOWN',v=>v.latest_run.input_revision=1,v=>v.current_card.bundle_id='old',
    v=>v.report.preparation_status='FAILED',
    v=>v.latest_run.output_narrative_id='old',v=>v.latest_run.nara.analysis_run_id='other']){
    const value=detail();value.verification={card_version_id:'c'};value.report.preparation_status='READY';change(value);
    assert.equal(reviewState(value).canConfirm,false);assert.equal(reviewState(value).canSubmit,false);
  }
});

test('Official reports stay read-only even when their historical source is valid',()=>{
  const value=detail();value.report.workflow_status='SUBMITTED';value.report.submitted_at='2026-10-23T00:00:00Z';
  assert.equal(reviewState(value).submitted,true);assert.equal(reviewState(value).canConfirm,false);
});

test('Partial corrections preserve untouched arrays and exact stored time, including milliseconds',()=>{
  const data={location_text:null,time_text:'pagi ini',occurred_at:'2026-10-23T01:02:03.456Z',
    involved_parties:[],impacts:['Baris sumber\nlanjutan'],victims:[],affected_objects:[]};
  const original=cardForm(data),values={...original,location_text:'Jalan Melati'};
  assert.deepEqual(correctionPatch(values,original),{location_text:'Jalan Melati'});
  assert.equal(data.occurred_at,'2026-10-23T01:02:03.456Z');
  assert.deepEqual(correctionPatch(original,original),{});
});

test('Explicit clearing remains null or an empty array; empty information does not become zero victims',()=>{
  const original=cardForm({location_text:'Jalan A',time_text:'pagi',victims:['Informasi dari sumber']});
  assert.deepEqual(correctionPatch({...original,location_text:'',victims:''},original),{location_text:null,victims:[]});
  assert.throws(()=>correctionPatch({...original,victims:'x'.repeat(501)},original),e=>e.code==='INVALID_PAYLOAD');
});

test('Lost submit/correction/confirmation responses read only the ledger and latest report, never POST',async()=>{
  for(const action of ['submit','cards/revisions','human-verifications','narratives/revisions']){
    const paths=[];
    const request={key:'key',report_id:'report',scope:`POST reports/report/${action}/`,state:'SUCCEEDED',result_type:'Card',result_id:'card'};
    const value=await readStoredReportAction(async path=>{paths.push(path);return {data:path.startsWith('requests/')?request:{report:{id:'report'}}};},'report','key');
    assert.deepEqual(paths,['requests/key/','reports/report/']);
    assert.equal(value.run,null);assert.match(reportRequestGuidance(value.request),/tersimpan/);
  }
});

test('Recovery includes report mutations but never combines a foreign report or run',async()=>{
  const mine={key:'k',report_id:'r',scope:'POST reports/r/submit/'};
  assert.deepEqual(reportRequests([mine,{...mine,report_id:'other'}],'r'),[mine]);
  await assert.rejects(readStoredReportAction(async()=>({data:{...mine,report_id:'other'}}),'r','k'),e=>e.code==='INVALID_RESPONSE');
});
