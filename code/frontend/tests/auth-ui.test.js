import test from 'node:test';
import assert from 'node:assert/strict';
import {challengeFromQuery, showLocalEmailHelp} from '../src/auth-ui.js';

test('Password reset link challenge accepts the canonical UUID supplied by the backend', () => {
  const id = 'a612f24d-0e65-4a5a-82c4-82607f8d2f82';
  assert.equal(challengeFromQuery(id), id);
  assert.equal(challengeFromQuery(id.toUpperCase()), id.toUpperCase());
});

test('Missing, malformed and duplicate challenge parameters cannot enable password reset', () => {
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

test('Registration carries only the email once into the code form', async()=>{
 const {rememberVerificationEmail,takeVerificationEmail}=await import('../src/auth-ui.js');
 rememberVerificationEmail('  person@example.test  ');
 assert.equal(takeVerificationEmail(),'person@example.test');
 assert.equal(takeVerificationEmail(),'');
});
test('Operator password form requires an explicit valid activation proof from the server',async()=>{
 const {accountVerificationResult}=await import('../src/auth-ui.js');
 const proof='a612f24d-0e65-4a5a-82c4-82607f8d2f82.'+'A'.repeat(43);
 assert.equal(accountVerificationResult({data:{message:'Selesai',next:'LOGIN'}}).next,'LOGIN');
 assert.equal(accountVerificationResult({data:{message:'Buat sandi',next:'SET_PASSWORD',activation_token:proof,expires_at:'2026-11-13T12:00:00Z'}}).activation_token,proof);
 for(const data of [{next:'OPERATOR',message:'Role'}, {next:'SET_PASSWORD',message:'Buat sandi'}, {next:'SET_PASSWORD',message:'Buat sandi',activation_token:proof,expires_at:'invalid'}, {next:'SET_PASSWORD',message:'Buat sandi',activation_token:'fake',expires_at:'2026-11-13T12:00:00Z'}])assert.throws(()=>accountVerificationResult({data}));
});
