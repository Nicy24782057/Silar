import test from 'node:test';
import assert from 'node:assert/strict';
import {adminReportsScope,ADMIN_REPORTS_PATH,ADMIN_REPORTS_TITLE,workspaceNavigation,dashboardCardLink,workspaceQuickView,workspaceReportsPath} from '../src/workspace.js';
const admin=permissions=>({role:'ADMIN',effective_permissions:permissions});
test('Merged Admin reports use the API scope permitted by the account',()=>{
 assert.equal(adminReportsScope(admin(['monitor_report'])),'monitor');
 assert.equal(adminReportsScope(admin(['assign_report'])),'assignment');
 assert.equal(adminReportsScope(admin(['monitor_report','assign_report'])),'assignment');
 assert.equal(adminReportsScope(admin([])),null);
 for(const user of [null,{role:'ADMIN'},{role:'REPORTER',effective_permissions:['monitor_report','assign_report']},{role:'OPERATOR',effective_permissions:['monitor_report','assign_report']}])assert.equal(adminReportsScope(user),null);
});
test('Monitoring and assignment have one navigation entry for either explicit Admin permission',()=>{
 for(const permissions of [['monitor_report'],['assign_report'],['monitor_report','assign_report']]){
  const links=workspaceNavigation(admin(permissions));
  assert.equal(links.filter(item=>item.to===ADMIN_REPORTS_PATH).length,1);
  assert.equal(links.find(item=>item.to===ADMIN_REPORTS_PATH).label,ADMIN_REPORTS_TITLE);
  assert(!links.some(item=>item.to==='/workspace/assignments'));
 }
 for(const user of [admin([]),{role:'OPERATOR',effective_permissions:['monitor_report','assign_report']}])assert(!workspaceNavigation(user).some(item=>item.to===ADMIN_REPORTS_PATH));
});
test('All report shortcuts share the merged page and keep their filters under either permitted API scope',()=>{
 for(const permissions of [['monitor_report'],['assign_report'],['monitor_report','assign_report']]){
  const user=admin(permissions),scope=adminReportsScope(user);
  for(const view of ['official','unassigned','closed']){
   assert.equal(dashboardCardLink(user,view),ADMIN_REPORTS_PATH+'?view='+view);
   const params=new URL(workspaceReportsPath(scope,workspaceQuickView(scope,view).filters),'https://silar.test').searchParams;
   assert.equal(params.get('scope'),scope);
   if(view==='unassigned'){assert.equal(params.get('unassigned'),'true');assert.equal(params.get('active'),'true');}
   if(view==='closed')assert.equal(params.get('workflow_status'),'CLOSED');
  }
 }
});
