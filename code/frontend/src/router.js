import { createRouter, createWebHistory } from 'vue-router';
import { session, restoreSession } from './session';
import { isStaff, hasPermission } from './workspace';
export const router = createRouter({history:createWebHistory(), routes:[
  {path:'/', redirect:'/reports'},
  ...[['/login','login'], ['/register','register'], ['/verify-email','verify'], ['/forgot-password','forgot'],
      ['/reset-password','reset'], ['/activate-operator','activate']].map(([path,mode]) => ({path, component:()=>import('./views/AuthView.vue'), meta:{mode}})),
  {path:'/reports', component:()=>import('./views/ReportsView.vue'), meta:{private:true, reporter:true}},
  {path:'/reports/:id', component:()=>import('./views/DraftView.vue'), meta:{private:true, reporter:true}},
  {path:'/profile', component:()=>import('./views/ProfileView.vue'), meta:{private:true}},
  {path:'/notifications', component:()=>import('./views/NotificationsView.vue'), meta:{private:true}},
  {path:'/workspace', component:()=>import('./views/WorkspaceView.vue'), meta:{private:true,staff:true,title:'Dashboard'}},
  ...[
    ['queue','queue','view_queue','Antrean Laporan'],['assigned','assigned','view_assigned_report','Penanganan Saya'],
    ['monitoring','monitor','monitor_report','Monitoring Laporan'],['assignments','assignment','assign_report','Penugasan']
  ].map(([path,scope,permission,title])=>({path:'/workspace/'+path,component:()=>import('./views/WorkspaceReportsView.vue'),
    meta:{private:true,staff:true,admin:['monitor','assignment'].includes(scope),permission,workspaceScope:scope,title}})),
  {path:'/workspace/operators',component:()=>import('./views/WorkspaceOperatorsView.vue'),meta:{private:true,staff:true,admin:true,permission:'manage_operator',title:'Manajemen Operator'}},
  {path:'/workspace/audit',component:()=>import('./views/WorkspaceAuditView.vue'),meta:{private:true,staff:true,permission:'view_audit',title:'Audit Aktivitas'}},
  {path:'/workspace/services',component:()=>import('./views/WorkspaceServicesView.vue'),meta:{private:true,staff:true,permission:'monitor_services',title:'Monitoring Layanan'}},
  {path:'/workspace/reports/:id',component:()=>import('./views/WorkspaceReportView.vue'),meta:{private:true,staff:true,title:'Detail Laporan'}},
  {path:'/pwa', component:()=>import('./views/PwaView.vue')},
  {path:'/:pathMatch(.*)*', component:()=>import('./views/NotFoundView.vue')}
]});
router.beforeEach(async to => {
  await restoreSession();
  if (to.meta.private && !session.user) return {path:'/login', query:{next:to.fullPath}};
  if (to.meta.reporter && session.user?.role !== 'REPORTER') return '/workspace';
  if (to.meta.staff && !isStaff(session.user)) return '/reports';
  if (to.meta.staff && (to.meta.admin&&session.user.role!=='ADMIN'||to.meta.permission&&!hasPermission(session.user,to.meta.permission))) return {path:'/workspace',query:{denied:'1'}};
});
router.afterEach(() => { document.title = 'SILAR — Pelaporan Kejadian'; });
