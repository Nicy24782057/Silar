import { createRouter, createWebHistory } from 'vue-router';
import { session, restoreSession } from './session';
export const router = createRouter({history:createWebHistory(), routes:[
  {path:'/', redirect:'/reports'},
  ...[['/login','login'], ['/register','register'], ['/verify-email','verify'], ['/forgot-password','forgot'],
      ['/reset-password','reset'], ['/activate-operator','activate']].map(([path,mode]) => ({path, component:()=>import('./views/AuthView.vue'), meta:{mode}})),
  {path:'/reports', component:()=>import('./views/ReportsView.vue'), meta:{private:true, reporter:true}},
  {path:'/reports/:id', component:()=>import('./views/DraftView.vue'), meta:{private:true, reporter:true}},
  {path:'/profile', component:()=>import('./views/ProfileView.vue'), meta:{private:true}},
  {path:'/notifications', component:()=>import('./views/NotificationsView.vue'), meta:{private:true}},
  {path:'/workspace', component:()=>import('./views/WorkspaceView.vue'), meta:{private:true}},
  {path:'/pwa', component:()=>import('./views/PwaView.vue')},
  {path:'/:pathMatch(.*)*', component:()=>import('./views/NotFoundView.vue')}
]});
router.beforeEach(async to => {
  await restoreSession();
  if (to.meta.private && !session.user) return {path:'/login', query:{next:to.fullPath}};
  if (to.meta.reporter && session.user?.role !== 'REPORTER') return '/workspace';
});
router.afterEach(() => { document.title = 'SILAR — Pelaporan Kejadian'; });
