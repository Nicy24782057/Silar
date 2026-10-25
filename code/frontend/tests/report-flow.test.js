import test from 'node:test';
import assert from 'node:assert/strict';
import {reportStageAccess} from '../src/report-flow.js';
function result(){
 const narrative={id:'n',bundle_id:'b',origin:'NORMALIZER'};
 return {report:{id:'r',input_revision:1,workflow_status:'NOT_SUBMITTED',preparation_status:'AWAITING_CONFIRMATION',current_card_version_id:'c',active_bundle_id:'b',active_narrative_id:'n'},
  current_card:{id:'c',bundle_id:'b',narrative_id:'n',sena_result_id:'s',nara_result_id:'a',data:{event_type:'FLOOD'}},active_narrative:narrative,verification:null,
  latest_run:{id:'run',status:'SUCCEEDED',bundle_id:'b',input_revision:1,output_narrative_id:'n',output_narrative:narrative,sena:{id:'s',category:'FLOOD',analysis_run_id:'run',narrative_id:'n'},nara:{id:'a',analysis_run_id:'run',narrative_id:'n'}}};
}
test('Fresh draft and saved evidence without a completed analysis keep stages 2 and 3 locked',()=>{
 for(const value of [null,{report:{id:'r',workflow_status:'NOT_SUBMITTED',preparation_status:'DRAFT'}},{...result(),current_card:null,latest_run:null}]){
  assert.equal(reportStageAccess(value).review,false);assert.equal(reportStageAccess(value).confirm,false);
 }
});
test('Completed current analysis opens review but confirmation requires advancing the exact card',()=>{
 const value=result();assert.equal(reportStageAccess(value).review,true);assert.equal(reportStageAccess(value).confirm,false);
 assert.equal(reportStageAccess(value,{advancedCardId:'c'}).confirm,true);
 assert.equal(reportStageAccess(value,{advancedCardId:'older'}).confirm,false);
});
test('Unsaved evidence and an open correction prevent jumping to confirmation',()=>{
 const value=result();assert.equal(reportStageAccess(value,{pendingInput:true,advancedCardId:'c'}).review,false);assert.equal(reportStageAccess(value,{pendingInput:true,advancedCardId:'c'}).confirm,false);
 assert.equal(reportStageAccess(value,{editingReview:true,advancedCardId:'c'}).review,true);assert.equal(reportStageAccess(value,{editingReview:true,advancedCardId:'c'}).confirm,false);
});
test('A corrected card invalidates local progress; legitimate stored verification allows resuming',()=>{
 const value=result();value.current_card.id='new';value.report.current_card_version_id='new';
 assert.equal(reportStageAccess(value,{advancedCardId:'c'}).confirm,false);
 value.verification={card_version_id:'new'};value.report.preparation_status='READY';assert.equal(reportStageAccess(value).confirm,true);
 value.verification.card_version_id='c';assert.equal(reportStageAccess(value).confirm,false);
});
test('Missing or mismatched result references and RUNNING/UNKNOWN/FAILED do not unlock review',()=>{
 for(const change of [v=>v.latest_run.status='RUNNING',v=>v.latest_run.status='UNKNOWN',v=>v.latest_run.status='FAILED',v=>v.latest_run.input_revision=2,v=>v.current_card.bundle_id='other',v=>v.latest_run.nara.analysis_run_id='other']){
  const value=result();change(value);const access=reportStageAccess(value,{advancedCardId:'c'});assert.equal(access.review,false);assert.equal(access.confirm,false);
 }
});
test('NON_EVENT remains readable at stage 2 while stage 3 stays locked',()=>{
 const value=result();value.latest_run.sena.category='NON_EVENT';value.current_card.data.event_type=null;value.report.preparation_status='BLOCKED';
 assert.equal(reportStageAccess(value).review,true);assert.equal(reportStageAccess(value,{advancedCardId:'c'}).confirm,false);
});
test('Saved narrative revision keeps reanalysis accessible but cannot unlock confirmation without new results',()=>{
 const value=result();value.current_card=null;value.report.current_card_version_id=null;value.report.active_narrative_id='n2';value.active_narrative={id:'n2',bundle_id:'b',origin:'REPORTER_REVISION'};
 assert.equal(reportStageAccess(value).review,true);assert.equal(reportStageAccess(value,{advancedCardId:'c'}).confirm,false);
 value.active_narrative.bundle_id='old';assert.equal(reportStageAccess(value).review,false);
});
test('Official reports remain readable through the steps without allowing another send',()=>{
 const value=result();value.report.workflow_status='SUBMITTED';value.report.submitted_at='2026-10-24T00:00:00Z';value.official_card=value.current_card;
 assert.equal(reportStageAccess(value).review,true);assert.equal(reportStageAccess(value).confirm,true);
});
