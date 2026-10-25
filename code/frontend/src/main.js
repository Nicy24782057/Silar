import { createApp } from 'vue';
import App from './App.vue';
import { router } from './router';
import { initializeTheme } from './theme';
import './theme.css';
import './style.css';
import './ui.css';
import './reports-ui.css';
import './auth-ui.css';
initializeTheme();
createApp(App).use(router).mount('#app');
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js').catch(() => {}); });
}
