import { ref } from 'vue';
export const online = ref(navigator.onLine);
window.addEventListener('online', () => online.value = true);
window.addEventListener('offline', () => online.value = false);
