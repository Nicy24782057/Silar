import { createApp } from 'vue';
import App from './App.vue';
import { router } from './router';
import { initializeTheme } from './theme';
import { restoreSession, session } from './session';
import './theme.css';
import './style.css';
import './ui.css';
import './reports-ui.css';
import './auth-ui.css';
import './workspace.css';
import './design-system.css';
import './public-ui.css';
import './fetch-state.css';
import './report-compose.css';
import './page-motion.css';
import './workspace-reference.css';
import './report-feedback.css';
import './navigation-ui.css';
import './auth-mobile.css';
import './mobile-reviewed.css';
initializeTheme();
const app=createApp(App).use(router);
router.isReady().then(async()=>{
  const mobile=matchMedia('(max-width:640px)').matches;
  const root=document.getElementById('app'),startup=document.getElementById('app-startup');
  if(mobile&&!session.ready)await restoreSession();
  if(mobile)root.inert=true;
  app.mount('#app');
  if(mobile){
    // Count preparation time toward the introduction, rather than delaying twice.
    const started=performance.getEntriesByName('silar-startup-visible')[0]?.startTime??0;
    await new Promise(resolve=>setTimeout(resolve,Math.max(0,1200-(performance.now()-started))));
    startup?.classList.add('startup-leaving');
    if(!matchMedia('(prefers-reduced-motion:reduce)').matches)await new Promise(resolve=>setTimeout(resolve,200));
    root.inert=false;
  }
  startup?.remove();
}).catch(()=>{
  const startup=document.getElementById('app-startup');startup?.classList.add('startup-error');startup?.setAttribute('role','alert');
  document.getElementById('startup-message').textContent='Aplikasi belum dapat dibuka. Periksa koneksi lalu muat ulang.';
  const retry=document.getElementById('startup-retry');retry.hidden=false;retry.addEventListener('click',()=>location.reload());
});
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js').catch(() => {}); });
}
