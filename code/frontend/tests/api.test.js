import test from 'node:test';
import assert from 'node:assert/strict';

let version = 0;
async function client(fetcher) {
  Object.defineProperty(globalThis, 'navigator', {configurable: true, value: {onLine: true}});
  globalThis.fetch = fetcher;
  return import(`../src/api.js?test=${++version}`);
}

test('Body sukses yang terputus setelah POST menahan hasil sebagai belum pasti tanpa retry', async () => {
  let calls = 0;
  const {api} = await client(async () => {calls++; return new Response('{"data":', {status: 201});});
  await assert.rejects(api('reports/r/analyses/', {method: 'POST', key: 'key', body: {mode: 'EVIDENCE'}}),
    error => error.code === 'RESPONSE_UNKNOWN' && error.status === 201);
  assert.equal(calls, 1);
});

test('Koneksi POST terputus tidak mengirim ulang request', async () => {
  let calls = 0;
  const {api} = await client(async () => {calls++; throw new TypeError('connection lost');});
  await assert.rejects(api('reports/r/analyses/', {method: 'POST', body: {}}),
    error => error.code === 'RESPONSE_UNKNOWN');
  assert.equal(calls, 1);
});

test('Respons gateway tanpa hasil backend pasti mengharuskan pembacaan keadaan tersimpan', async () => {
  for (const response of [new Response('<html>gateway timeout</html>', {status: 504}),
    new Response(JSON.stringify({error: {code: 'BACKEND_UNAVAILABLE'}}), {status: 503})]) {
    const {api} = await client(async () => response);
    await assert.rejects(api('reports/r/analyses/', {method: 'POST', body: {}}),
      error => error.code === 'RESPONSE_UNKNOWN');
  }
});

test('Kegagalan AI yang telah dicatat mempertahankan kode backend', async () => {
  const {api} = await client(async () => new Response(JSON.stringify({error: {
    code: 'AI_UPSTREAM_FAILED', message: 'Layanan narasi gagal.', request_id: 'trace',
  }}), {status: 502}));
  await assert.rejects(api('reports/r/analyses/', {method: 'POST', body: {}}),
    error => error.code === 'AI_UPSTREAM_FAILED' && error.requestId === 'trace');
});

test('Body GET yang tidak terbaca tidak menyatakan mutasi telah dilakukan', async () => {
  const {api} = await client(async () => new Response('{', {status: 200}));
  await assert.rejects(api('requests/'), error => error.code === 'NETWORK_ERROR');
});

test('Logout 204 tidak mencoba membaca JSON', async () => {
  const {api} = await client(async () => new Response(null, {status: 204}));
  assert.equal(await api('auth/logout/', {method: 'POST', body: {}}), null);
});
