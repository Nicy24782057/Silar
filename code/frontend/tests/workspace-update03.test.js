import test from 'node:test';
import assert from 'node:assert/strict';
import {dashboardCardLink,workspaceQuickView,workspaceReportsPath,operatorStatusFilter,workspaceEffectiveFilters} from '../src/workspace.js';
const admin={role:'ADMIN',effective_permissions:['monitor_report','assign_report','manage_operator']};
test('Four Admin cards open their own matching report and account destinations',()=>{
 const expected={official:'/workspace/monitoring?view=official',unassigned:'/workspace/monitoring?view=unassigned',operators:'/workspace/operators?status=active',closed:'/workspace/monitoring?view=closed'};
 for(const [key,url]of Object.entries(expected))assert.equal(dashboardCardLink(admin,key),url);
});
test('Admin shortcut routing uses explicit permissions and does not grant them by role',()=>{
 const monitor={role:'ADMIN',effective_permissions:['monitor_report']},assign={role:'ADMIN',effective_permissions:['assign_report']};
 assert.equal(dashboardCardLink(monitor,'unassigned'),'/workspace/monitoring?view=unassigned');
 assert.equal(dashboardCardLink(monitor,'operators'),null);
 assert.equal(dashboardCardLink(assign,'official'),'/workspace/monitoring?view=official');
 assert.equal(dashboardCardLink(assign,'closed'),'/workspace/monitoring?view=closed');
 for(const key of ['official','unassigned','operators','closed']){
  assert.equal(dashboardCardLink({...admin,effective_permissions:[]},key),null);
  assert.equal(dashboardCardLink({...admin,role:'OPERATOR'},key),null);
  assert.equal(dashboardCardLink({...admin,role:'REPORTER'},key),null);
 }
});
test('Admin views preserve all official reports, current unassigned state and CLOSED separately',()=>{
 for(const scope of ['monitor','assignment']){
  assert.deepEqual(workspaceQuickView(scope,'official').filters,{});
  assert.deepEqual(workspaceQuickView(scope,'unassigned').filters,{active:'true',unassigned:'true'});
  assert.deepEqual(workspaceQuickView(scope,'closed').filters,{workflow_status:'CLOSED'});
  const q=new URL(workspaceReportsPath(scope,{...workspaceQuickView(scope,'unassigned').filters,page:2}),'https://silar.test').searchParams;
  assert.equal(q.get('scope'),scope);assert.equal(q.get('unassigned'),'true');assert.equal(q.get('active'),'true');assert.equal(q.get('page'),'2');
 }
 assert.equal(workspaceQuickView('assigned','closed'),null);
 for(const value of ['__proto__','constructor',['closed'],null])assert.equal(workspaceQuickView('monitor',value),null);
});
test('Operator account status links accept only supported single query values',()=>{
 for(const value of ['active','pending','inactive'])assert.equal(operatorStatusFilter(value),value);
 for(const value of [undefined,null,['active'],'ACTIVE','all','__proto__'])assert.equal(operatorStatusFilter(value),'');
});
test('Empty or stale form values cannot erase a fixed CLOSED dashboard filter',()=>{
 const closed=workspaceQuickView('monitor','closed');
 for(const status of ['','ASSIGNED']){
  const filters=workspaceEffectiveFilters({workflow_status:status,event_type:'FIRE',ordering:'submitted_at'},closed);
  const q=new URL(workspaceReportsPath('monitor',filters),'https://silar.test').searchParams;
  assert.equal(q.get('workflow_status'),'CLOSED');assert.equal(q.get('event_type'),'FIRE');assert.equal(q.get('ordering'),'submitted_at');
 }
 assert.deepEqual(workspaceEffectiveFilters({workflow_status:'ASSIGNED'},null),{workflow_status:'ASSIGNED'});
});
