import { reactive } from 'vue';

const preferenceKey = 'silar-theme';
const valid = value => value === 'light' || value === 'dark';
export const theme = reactive({ mode: 'light' });
let manual = null;
let initialized = false;
let media = null;

function apply(mode) {
  theme.mode = mode;
  document.documentElement.dataset.theme = mode;
  document.documentElement.style.colorScheme = mode;
  const color = document.querySelector('meta[name="theme-color"]');
  if (color) color.content = mode === 'dark' ? '#0B1220' : '#F5F8FC';
}

export function initializeTheme() {
  if (initialized) return;
  initialized = true;
  media = window.matchMedia?.('(prefers-color-scheme: dark)') || null;
  try {
    const saved = window.localStorage.getItem(preferenceKey);
    manual = valid(saved) ? saved : null;
  } catch { /* Browser storage can be unavailable; the in-memory choice works. */ }
  apply(manual || (media?.matches ? 'dark' : 'light'));
  media?.addEventListener?.('change', event => {
    if (!manual) apply(event.matches ? 'dark' : 'light');
  });
  window.addEventListener('storage', event => {
    if (event.key !== preferenceKey && event.key !== null) return;
    manual = valid(event.newValue) ? event.newValue : null;
    apply(manual || (media?.matches ? 'dark' : 'light'));
  });
}

export function toggleTheme() {
  manual = theme.mode === 'dark' ? 'light' : 'dark';
  apply(manual);
  try { window.localStorage.setItem(preferenceKey, manual); }
  catch { /* Preserve the manual choice in memory without interrupting forms. */ }
}
