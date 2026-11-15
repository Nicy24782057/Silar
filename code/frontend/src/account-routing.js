export function accountHome(user) {
  return user?.role === 'REPORTER' ? '/reports' :
    ['OPERATOR', 'ADMIN'].includes(user?.role) ? '/workspace' : '/login';
}

export function loginDestination(next, user) {
  const home = accountHome(user);
  if (typeof next !== 'string' || !next.startsWith('/') || next.startsWith('//') || /[\\\u0000-\u0020]/.test(next)) return home;
  const base = 'https://silar.invalid';
  let url;
  try { url = new URL(next, base); } catch { return home; }
  const path = url.pathname.replace(/\/+$/, '') || '/';
  if (url.origin !== base || ['/login', '/register', '/verify-email', '/activate-operator', '/forgot-password', '/reset-password'].includes(path)) return home;
  return url.pathname + url.search + url.hash;
}
