const API_BASE = (import.meta.env.VITE_API_BASE || '/api/v1/').replace(/\/?$/, '/');
let access = null;
let csrf = null;
let csrfWork = null;
let refreshWork = null;
let clearHandler = () => {};

export class ApiError extends Error {
  constructor(message, code, status = 0, fields = {}, requestId = null, retryAfter = null) {
    super(message); Object.assign(this, {code, status, fields, requestId, retryAfter});
  }
}
export function onSessionExpired(callback) { clearHandler = callback; }
export function clearAccess() { access = null; }

async function send(path, options = {}) {
  const {method = 'GET', body, auth = true, raw = false, retryRead = true, csrfToken} = options;
  if (!navigator.onLine) throw new ApiError('Sambungkan internet untuk menggunakan layanan laporan.', 'OFFLINE');
  const headers = {};
  if (auth && access) headers.Authorization = 'Bearer ' + access;
  if (csrfToken) headers['X-CSRFToken'] = csrfToken;
  if (options.key) headers['Idempotency-Key'] = options.key;
  const multipart = body instanceof FormData;
  if (body !== undefined && !multipart) headers['Content-Type'] = 'application/json';
  let response;
  try {
    response = await fetch(API_BASE + path.replace(/^\//, ''), {method, headers, credentials:'include', cache:'no-store',
      body: body === undefined ? undefined : multipart ? body : JSON.stringify(body)});
  } catch {
    throw new ApiError(method === 'GET' ? 'Layanan belum dapat dibaca. Periksa koneksi, lalu muat kembali.' :
      'Respons terputus. Hasil tindakan belum pasti. Baca keadaan tersimpan sebelum mengulang.',
      method === 'GET' ? 'NETWORK_ERROR' : 'RESPONSE_UNKNOWN');
  }
  if (response.status === 401 && auth && method === 'GET' && retryRead) {
    try { await refresh(); return send(path, {...options, retryRead:false}); }
    catch (error) { clearAccess(); clearHandler(); throw error; }
  }
  if (!response.ok) {
    let data = {};
    try { data = await response.json(); } catch { /* Safe HTTP fallback below. */ }
    const error = data.error || {};
    if (response.status === 401 && auth) { clearAccess(); clearHandler(); }
    throw new ApiError(error.message || 'Layanan belum dapat digunakan.', error.code || 'HTTP_ERROR', response.status,
      error.fields || {}, error.request_id, response.headers.get('Retry-After'));
  }
  if (raw) return response.blob();
  if (response.status === 204) return null;
  return response.json();
}

async function getCsrf() {
  if (!csrfWork) csrfWork = send('auth/csrf/', {auth:false}).then(result => csrf = result.data.csrf_token).finally(() => csrfWork = null);
  return csrfWork;
}
export async function authPost(path, body) {
  const token = await getCsrf();
  return send('auth/' + path, {method:'POST', auth:false, body, csrfToken:token});
}
export async function refresh() {
  if (!refreshWork) refreshWork = authPost('refresh/', {}).then(result => { access = result.data.access; return result; }).finally(() => refreshWork = null);
  return refreshWork;
}
export async function login(email, password) {
  const result = await authPost('login/', {email, password});
  access = result.data.access;
  return (await send('me/')).data;
}
export async function logout() {
  try { await authPost('logout/', {}); } finally { clearAccess(); }
}
export const api = send;
