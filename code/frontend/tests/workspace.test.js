import test from 'node:test';
import assert from 'node:assert/strict';
import {workspaceNavigation,handlerCan,closeAllowed,decisionAllowed,personName,workspaceReportsPath,assignmentTargetAvailable} from '../src/workspace.js';
const operator={id:'andi-id',role:'OPERATOR',full_name:'Andi Pratama',effective_permissions:['view_queue','view_assigned_report','claim_report','review_report','manage_followup','publish_report','close_report']};
const detail={private_access:true,assignment:{operator_id:'andi-id'},report:{workflow_status:'IN_REVIEW',validation_status:'VALID',publication_status:'INTERNAL'},reviews:[{}],has_active_candidate:false,close_requirements:[{met:true},{met:true},{met:true},{met:true}]};
test('Assignee labels follow account names rather than fixed Operator A/B/C slots',()=>{
 assert.equal(personName({full_name:'Andi Pratama'}),'Andi Pratama');
 assert.equal(personName({operator_name:'Rina Lestari'}),'Rina Lestari');
 assert.equal(personName(null),'Belum ditugaskan');
});
test('Pure Admin navigation has management but no inherited Operator actions',()=>{
 const admin={role:'ADMIN',effective_permissions:['manage_operator','assign_report','monitor_report','view_audit','monitor_services']};
 const urls=workspaceNavigation(admin).map(x=>x.to);
 assert(urls.includes('/workspace/operators'));assert(urls.includes('/workspace/monitoring'));assert(!urls.includes('/workspace/assignments'));
 assert(!urls.includes('/workspace/queue'));assert(!urls.includes('/workspace/assigned'));
 assert.equal(handlerCan(admin,detail,'review_report'),false);
});
test('A role label cannot grant private reading or mutation after reassignment',()=>{
 assert.equal(handlerCan(operator,detail,'review_report'),true);
 assert.equal(handlerCan(operator,{...detail,assignment:{operator_id:'rina-id'}},'review_report'),false);
 assert.equal(handlerCan(operator,{...detail,private_access:false},'review_report'),false);
 assert.equal(handlerCan({...operator,effective_permissions:[]},detail,'review_report'),false);
});
test('Closed reports and unmet close requirements never enable a mutation',()=>{
 assert.equal(closeAllowed(operator,detail),true);
 assert.equal(closeAllowed(operator,{...detail,close_requirements:[{met:false}]}),false);
 assert.equal(handlerCan(operator,{...detail,report:{workflow_status:'CLOSED'}},'close_report'),false);
});
test('Prepare requires valid review and cannot alter published or active-candidate state',()=>{
 assert.equal(decisionAllowed(detail,'PREPARE'),true);
 for(const outcome of ['INVALID','INCONCLUSIVE'])assert.equal(decisionAllowed({...detail,report:{...detail.report,validation_status:outcome}},'PREPARE'),false);
 assert.equal(decisionAllowed({...detail,has_active_candidate:true},'INTERNAL'),false);
 assert.equal(decisionAllowed({...detail,report:{...detail.report,publication_status:'PUBLISHED'}},'INTERNAL'),false);
});
test('Workspace filters remain server-scoped and preserve independent states',()=>{
 const url=new URL(workspaceReportsPath('assigned',{event_type:'FIRE',workflow_status:'FOLLOW_UP',page:2}),'https://silar.test/');
 assert.deepEqual(Object.fromEntries(url.searchParams),{scope:'assigned',page_size:'10',ordering:'-submitted_at',event_type:'FIRE',workflow_status:'FOLLOW_UP',page:'2'});
 assert.throws(()=>workspaceReportsPath('owned'));
 assert.equal(assignmentTargetAvailable({id:'andi-id'},'andi-id'),false);
});
