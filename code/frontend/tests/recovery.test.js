import test from 'node:test';
import assert from 'node:assert/strict';
import {analysisRequests, readStoredAnalysis, requestGuidance, requiresStoredState} from '../src/recovery.js';

const record = {key: 'key', report_id: 'report', scope: 'POST reports/report/analyses/',
  result_type: 'Run', result_id: 'run', state: 'SUCCEEDED'};

test('Pembacaan respons hilang memakai GET request, run dan draft tanpa POST atau replay otomatis', async () => {
  const paths = [];
  const result = await readStoredAnalysis(async path => {
    paths.push(path);
    return {data: path.startsWith('requests/') ? record : path.includes('analysis-runs/') ?
      {id: 'run', report_id: 'report', status: 'SUCCEEDED'} : {report: {id: 'report'}}};
  }, 'report', 'key');
  assert.deepEqual(paths, ['requests/key/', 'reports/report/analysis-runs/run/', 'reports/report/']);
  assert.equal(result.run.id, 'run');
});

test('RUNNING dan UNKNOWN tanpa hasil terminal hanya dibaca tanpa menebak run atau mengulang', async () => {
  for (const state of ['RUNNING', 'UNKNOWN']) {
    const paths = [];
    const result = await readStoredAnalysis(async path => {
      paths.push(path);
      return {data: path.startsWith('requests/') ? {...record, state, result_type: null, result_id: null} :
        {report: {id: 'report'}}};
    }, 'report', 'key');
    assert.deepEqual(paths, ['requests/key/', 'reports/report/']);
    assert.equal(result.run, null);
    assert.match(requestGuidance(state), /jangan kirim|ditahan/);
  }
});

test('Request dan run dari laporan lain tidak digabungkan ke draft yang dibuka', async () => {
  let calls = 0;
  await assert.rejects(readStoredAnalysis(async () => {calls++; return {data: {...record, report_id: 'other'}};},
    'report', 'key'), error => error.code === 'INVALID_RESPONSE');
  assert.equal(calls, 1);
  await assert.rejects(readStoredAnalysis(async path => ({data: path.startsWith('requests/') ? record :
    {id: 'run', report_id: 'other'}}), 'report', 'key'), error => error.code === 'INVALID_RESPONSE');
});

test('Daftar pemulihan analisis menyaring request upload dan laporan lain', () => {
  const rows = [record, {...record, key: 'upload', scope: 'POST reports/report/evidence/'},
    {...record, key: 'other', report_id: 'other'}];
  assert.deepEqual(analysisRequests(rows, 'report'), [record]);
});

test('Respons hilang, REQUEST_RUNNING dan REQUEST_UNKNOWN menahan tindakan baru sampai dibaca', () => {
  for (const code of ['RESPONSE_UNKNOWN', 'REQUEST_RUNNING', 'REQUEST_UNKNOWN'])
    assert.equal(requiresStoredState({code}), true);
  assert.equal(requiresStoredState({code: 'AI_UPSTREAM_FAILED'}), false);
});
