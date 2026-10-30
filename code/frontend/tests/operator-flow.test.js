import test from 'node:test';
import assert from 'node:assert/strict';
import {savedReview,canDraftPublication,publicationValues,publicationReceipt,publicationRequest,reviewedPublicationCandidate} from '../src/operator-flow.js';

const packet={id:'report',body:{outcome:'VALID',reason:'Sumber sesuai.'},reviewContext:{previousIds:['old'],cardId:'official',operatorId:'operator'}};
const row={id:'new',card_version_id:'official',operator_id:'operator',outcome:'VALID',reason:'Sumber sesuai.'};
const detail={report:{id:'report'},private_access:true,reviews:[row]};
test('Review success requires a newly stored matching review, official source and current operator',()=>{
 assert.equal(savedReview(detail,packet),row);
 for(const modified of [{...detail,private_access:false},{...detail,report:{id:'other'}},{...detail,reviews:[{...row,id:'old'}]},
  {...detail,reviews:[{...row,card_version_id:'other'}]},{...detail,reviews:[{...row,operator_id:'other'}]},
  {...detail,reviews:[{...row,outcome:'INVALID'}]},{...detail,reviews:[{...row,reason:'Berbeda'}]}])assert.equal(savedReview(modified,packet),null);
});
test('Publication editor only opens for a Valid review of the exact official card with no active candidate',()=>{
 const value={report:{workflow_status:'IN_REVIEW',validation_status:'VALID',official_card_version_id:'card',publication_status:'NOT_DECIDED'},latest_review:{outcome:'VALID',card_version_id:'card'},official_card:{id:'card'}};
 for(const publication_status of ['NOT_DECIDED','INTERNAL','PENDING_APPROVAL','PUBLISHED'])assert.equal(canDraftPublication({...value,report:{...value.report,publication_status}}),true);
 for(const modified of [{...value,active_candidate:{id:'candidate'}},{...value,latest_review:{outcome:'INVALID',card_version_id:'card'}},
  {...value,latest_review:{outcome:'VALID',card_version_id:'old'}},{...value,official_card:{id:'other'}},
  {...value,report:{...value.report,workflow_status:'CLOSED'}},{...value,report:{...value.report,validation_status:'INCONCLUSIVE'}},
  {...value,report:{...value.report,publication_status:'APPROVED'}}])assert.equal(canDraftPublication(modified),false);
});
test('Public draft values exclude private fields and preserve unknown values as null',()=>{
 const result=publicationValues({summary:'  Ringkasan publik  ',general_location:' ',occurred_at:'2026-10-30T15:00:00+07:00',owner:'secret',evidence:['private'],event_type:'FIRE'});
 assert.deepEqual(result,{summary:'Ringkasan publik',general_location:null,time_text:null,occurred_at:'2026-10-30T08:00:00.000Z',general_impact:null,handling_update:null});
 assert.throws(()=>publicationValues({summary:'   '}),e=>e.code==='INVALID_PAYLOAD');
 for(const occurred_at of ['2026-10-30T15:00:00','bad'])assert.throws(()=>publicationValues({summary:'Isi',occurred_at}),e=>e.code==='INVALID_PAYLOAD');
});
test('A successful HTTP response cannot advance publication without the exact report, revision and version receipt',()=>{
 const target={reportId:'report',action:'create',body:{expected_revision:8}};
 const response={data:{report:{id:'report',revision:9},object:{id:'version',state:'DRAFT'}}};
 assert.equal(publicationReceipt(response,target),response.data);
 for(const bad of [{data:{...response.data,report:{id:'other',revision:9}}},{data:{...response.data,report:{id:'report',revision:8}}},
  {data:{...response.data,object:{state:'DRAFT'}}},{data:{...response.data,object:{id:'version',state:'APPROVED'}}}])assert.throws(()=>publicationReceipt(bad,target),e=>e.code==='RESPONSE_UNKNOWN');
 assert.throws(()=>publicationReceipt(response,{...target,action:'approve',versionId:'other'}),e=>e.code==='RESPONSE_UNKNOWN');
});
test('Publication recovery is bound to the original idempotency key, report and operation',()=>{
 const target={key:'key',reportId:'report',scope:'publication.publish:version:report'};
 const record={key:'key',report_id:'report',scope:target.scope,state:'SUCCEEDED'};
 assert.equal(publicationRequest(record,target),record);
 for(const bad of [{...record,key:'other'},{...record,report_id:'other'},{...record,scope:'publication.approve:version:report'}])assert.throws(()=>publicationRequest(bad,target),e=>e.code==='INVALID_RESPONSE');
});

test('Guided confirmation only approves a stored candidate with exactly the reviewed public content',()=>{
 const values=publicationValues({summary:'Isi yang telah diperiksa',occurred_at:'2026-10-30T15:00:00+07:00'});
 const candidate={id:'candidate',state:'DRAFT',card_version_id:'card',data:{event_type:'FLOOD',...values,occurred_at:'2026-10-30T08:00:00Z'}};
 const detail={report:{official_card_version_id:'card'},active_candidate:candidate};
 assert.equal(reviewedPublicationCandidate(detail,'candidate',values,'FLOOD'),candidate);
 for(const candidateChange of [{...candidate,id:'different'},{...candidate,state:'APPROVED'},{...candidate,card_version_id:'other'},
  {...candidate,data:{...candidate.data,summary:'Changed content'}},{...candidate,data:{...candidate.data,event_type:'FIRE'}},
  {...candidate,data:{...candidate.data,owner:'private'}},{...candidate,data:{...candidate.data,occurred_at:'2026-10-30T09:00:00Z'}}])
  assert.throws(()=>reviewedPublicationCandidate({...detail,active_candidate:candidateChange},'candidate',values,'FLOOD'),e=>e.code==='VERSION_CONFLICT');
});
