export function challengeFromQuery(value) {
  return typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value) ? value : '';
}

export function showLocalEmailHelp({flag, development = false, hostname = ''} = {}) {
  if (flag === 'true') return true;
  if (flag === 'false') return false;
  return development && ['localhost', '127.0.0.1', '[::1]', '::1'].includes(hostname);
}
