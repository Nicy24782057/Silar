import { createApp } from 'vue';
import App from './App.vue';
import { router } from './router';
import { initializeTheme } from './theme';
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
initializeTheme();
createApp(App).use(router).mount('#app');
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js').catch(() => {}); });
}
