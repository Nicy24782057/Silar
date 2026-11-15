import { reactive } from 'vue';
import { api, refresh, login, logout, clearAccess, onSessionExpired } from './api.js';
export const session = reactive({user:null, ready:false, message:'', restoreError:null});
onSessionExpired(() => { session.user = null; session.restoreError = null; session.message = 'Sesi berakhir. Silakan masuk kembali.'; });
let boot;
export function restoreSession({retry = false} = {}) {
  if (retry && session.ready && session.restoreError) boot = null;
  if (!boot) boot = (async () => {
    session.ready = false; session.restoreError = null; session.message = '';
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try { await refresh({signal:controller.signal}); session.user = (await api('me/', {signal:controller.signal, retryRead:false})).data; session.message = ''; }
    catch (error) {
      clearAccess(); session.user = null;
      if (error.status !== 401) {
        session.restoreError = error;
        session.message = error.name === 'AbortError' ? 'Pemeriksaan sesi belum selesai. Periksa koneksi lalu coba lagi.' :
          error.code === 'OFFLINE' ? 'Perangkat offline. Sambungkan jaringan untuk memeriksa sesi.' : error.message;
      }
    }
    finally { clearTimeout(timeout); session.ready = true; }
  })();
  return boot;
}
export async function signIn(email, password) { session.user = await login(email, password); session.ready = true; session.restoreError = null; session.message = ''; }
export async function signOut() {
  try { await logout(); session.message = ''; }
  catch (error) { session.message = 'Sesi pada perangkat dibersihkan. Logout di server belum dapat dipastikan; periksa koneksi dan coba kembali.'; }
  finally { session.user = null; session.restoreError = null; session.ready = true; }
}
