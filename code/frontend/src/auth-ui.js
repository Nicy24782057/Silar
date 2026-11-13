export function challengeFromQuery(value) {
  return typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value) ? value : '';
}

export function showLocalEmailHelp({flag, development = false, hostname = ''} = {}) {
  if (flag === 'true') return true;
  if (flag === 'false') return false;
  return development && ['localhost', '127.0.0.1', '[::1]', '::1'].includes(hostname);
}

// Only the email is held during the immediate registration -> verification move.
// Passwords, codes and activation proofs never enter persistent browser storage.
let verificationEmail = '';
export function rememberVerificationEmail(email) { verificationEmail = String(email || '').trim(); }
export function takeVerificationEmail() { const value = verificationEmail; verificationEmail = ''; return value; }
export function accountVerificationResult(response) {
  const data = response?.data;
  if (data?.next === 'LOGIN' && typeof data.message === 'string') return data;
  if (data?.next === 'SET_PASSWORD' && typeof data.message === 'string' &&
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.[A-Za-z0-9_-]{43}$/.test(data.activation_token) &&
      typeof data.expires_at === 'string' && Number.isFinite(Date.parse(data.expires_at))) return data;
  throw new Error('Hasil verifikasi belum dapat dipastikan. Periksa kembali sebelum melanjutkan.');
}
