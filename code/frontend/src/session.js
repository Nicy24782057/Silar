import { reactive } from 'vue';
import { api, refresh, login, logout, onSessionExpired } from './api';
export const session = reactive({user:null, ready:false, message:''});
onSessionExpired(() => { session.user = null; session.message = 'Sesi berakhir. Silakan masuk kembali.'; });
let boot;
export function restoreSession() {
  if (!boot) boot = (async () => {
    try { await refresh(); session.user = (await api('me/')).data; }
    catch (error) { if (error.status !== 401 && error.code !== 'OFFLINE') session.message = error.message; }
    finally { session.ready = true; }
  })();
  return boot;
}
export async function signIn(email, password) { session.user = await login(email, password); session.message = ''; }
export async function signOut() {
  try { await logout(); session.message = ''; }
  catch (error) { session.message = 'Sesi pada perangkat dibersihkan. Logout di server belum dapat dipastikan; periksa koneksi dan coba kembali.'; }
  finally { session.user = null; }
}
