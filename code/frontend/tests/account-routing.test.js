import test from 'node:test';
import assert from 'node:assert/strict';
import {accountHome,loginDestination} from '../src/account-routing.js';

test('Akun aktif kembali ke ruang sesuai peran, tanpa formulir login',()=>{
  for(const role of ['REPORTER','OPERATOR','ADMIN']){
    const home=role==='REPORTER'?'/reports':'/workspace';
    assert.equal(accountHome({role}),home);
    assert.equal(loginDestination(undefined,{role}),home);
  }
  assert.equal(accountHome(null),'/login');
});

test('Tujuan login mempertahankan alamat lokal dan menolak origin lain serta loop autentikasi',()=>{
  const user={role:'REPORTER'};
  assert.equal(loginDestination('/reports/report-id?view=review#card',user),'/reports/report-id?view=review#card');
  for(const next of ['https://example.test','//example.test','/\\example.test','/\n/example.test','/login','/login/?next=/login','/a/../login','/register','/verify-email','/forgot-password','/reset-password?challenge_id=x',[]])
    assert.equal(loginDestination(next,user),'/reports',String(next));
});
