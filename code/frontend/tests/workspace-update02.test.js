import test from 'node:test';
import assert from 'node:assert/strict';
import {dashboardCardLink,workspaceQuickView,workspaceReportsPath,reportTabLocked} from '../src/workspace.js';
const operator={role:'OPERATOR',effective_permissions:['view_queue','view_assigned_report']};
test('Four metric links use separate destinations and respect read permissions',()=>{
 for(const [key,url]of Object.entries({queue:'/workspace/queue',assigned:'/workspace/assigned?view=active',review_pending:'/workspace/assigned?view=review',followup_pending:'/workspace/assigned?view=followup'})){
  assert.equal(dashboardCardLink(operator,key),url);
  assert.equal(dashboardCardLink({...operator,effective_permissions:[]},key),null);
  assert.equal(dashboardCardLink({...operator,role:'REPORTER'},key),null);
 }
 assert.equal(dashboardCardLink(operator,'__proto__'),null);
});
test('Shortcut filters preserve scope and pagination without accepting inherited object keys',()=>{
 const review=workspaceQuickView('assigned','review');
 const q=new URL(workspaceReportsPath('assigned',{...review.filters,page:2,event_type:'FIRE'}),'https://silar.test').searchParams;
 assert.equal(q.get('scope'),'assigned');assert.equal(q.get('validation_status'),'NOT_REVIEWED');
 assert.equal(q.get('active'),'true');assert.equal(q.get('page'),'2');assert.equal(q.get('event_type'),'FIRE');
 assert.deepEqual(workspaceQuickView('assigned','followup').filters,{active:'true',followup_status:'PENDING'});
 assert.equal(workspaceQuickView('queue','review'),null);
 for(const key of ['__proto__','constructor','unknown',null,['review']])assert.equal(workspaceQuickView('assigned',key),null);
});
test('Unsaved review text never unlocks dependent tabs',()=>{
 const pending={report:{official_card_version_id:'card',validation_status:'NOT_REVIEWED'},reviews:[],review:{outcome:'VALID',reason:'Unsaved text'}};
 for(const tab of ['followup','decision']){
  assert.equal(reportTabLocked(null,tab),true);assert.equal(reportTabLocked(pending,tab),true);
  assert.equal(reportTabLocked({...pending,reviews:[{card_version_id:'card'}]},tab),true);
 }
 for(const tab of ['summary','evidence','review','history'])assert.equal(reportTabLocked(pending,tab),false);
});
test('All saved outcomes unlock dependent reading, including CLOSED; old-card reviews do not',()=>{
 for(const outcome of ['VALID','INVALID','INCONCLUSIVE']){
  const detail={report:{official_card_version_id:'card',validation_status:outcome,workflow_status:'IN_REVIEW'},reviews:[{card_version_id:'card'}]};
  for(const tab of ['followup','decision']){
   assert.equal(reportTabLocked(detail,tab),false);
   assert.equal(reportTabLocked({...detail,report:{...detail.report,workflow_status:'CLOSED'}},tab),false);
   assert.equal(reportTabLocked({...detail,reviews:[{card_version_id:'old-card'}]},tab),true);
  }
 }
});
