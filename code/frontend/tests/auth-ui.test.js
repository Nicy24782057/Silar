import test from 'node:test';
import assert from 'node:assert/strict';
import {challengeFromQuery, showLocalEmailHelp} from '../src/auth-ui.js';

test('Email link challenge accepts the canonical UUID supplied by the backend', () => {
  const id = 'a612f24d-0e65-4a5a-82c4-82607f8d2f82';
  assert.equal(challengeFromQuery(id), id);
  assert.equal(challengeFromQuery(id.toUpperCase()), id.toUpperCase());
});

test('Missing, malformed and duplicate challenge parameters cannot enable verification', () => {
  const id = 'a612f24d-0e65-4a5a-82c4-82607f8d2f82';
  for (const value of [null, undefined, '', [], [id], [id,id], {}, ' '+id, id+' ', 'urn:uuid:'+id, 'https://example.test/'+id, id.slice(1)]) {
    assert.equal(challengeFromQuery(value), '');
  }
});

test('Local email help defaults to development running on loopback, never a public deployment', () => {
  for (const hostname of ['localhost','127.0.0.1','::1','[::1]']) {
    assert.equal(showLocalEmailHelp({development:true,hostname}), true);
    assert.equal(showLocalEmailHelp({development:false,hostname}), false);
  }
  for (const hostname of ['silar.example','localhost.example','192.168.1.5']) {
    assert.equal(showLocalEmailHelp({development:true,hostname}), false);
  }
});

test('An explicit local-help setting controls local preview without inferring backend email delivery', () => {
  assert.equal(showLocalEmailHelp({flag:'true'}), true);
  assert.equal(showLocalEmailHelp({flag:'false',development:true,hostname:'localhost'}), false);
  assert.equal(showLocalEmailHelp({flag:'unrecognized',development:false}), false);
});
