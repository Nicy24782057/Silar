import test from 'node:test';
import assert from 'node:assert/strict';
import { categoryFilters, reportsPath, reportStatus, REPORT_PAGE_SIZE } from '../src/report-list.js';

test('Four actual incident categories include earthquake; NON_EVENT is not an event category', () => {
  assert.deepEqual(categoryFilters.filter(item=>['FLOOD','EARTHQUAKE','FIRE','ACCIDENT'].includes(item.value)).map(item=>item.value), ['FLOOD','EARTHQUAKE','FIRE','ACCIDENT']);
  assert.equal(categoryFilters.find(item=>item.value==='EARTHQUAKE').label, 'Gempa Bumi');
  assert.equal(categoryFilters.some(item=>item.value==='NON_EVENT'), false);
});

test('Prepared drafts combine category and both states in a paginated server query', () => {
  const url = new URL(reportsPath('AWAITING_CONFIRMATION','created_at','EARTHQUAKE',2),'https://silar.test/');
  assert.deepEqual(Object.fromEntries(url.searchParams), {scope:'owned',ordering:'created_at',page_size:String(REPORT_PAGE_SIZE),workflow_status:'NOT_SUBMITTED',preparation_status:'AWAITING_CONFIRMATION',event_type:'EARTHQUAKE',page:'2'});
  const submitted = new URL(reportsPath('SUBMITTED','-created_at','FIRE'),'https://silar.test/');
  assert.equal(submitted.searchParams.get('workflow_status'),'SUBMITTED');
  assert.equal(submitted.searchParams.has('preparation_status'),false);
  assert.throws(()=>reportsPath('DONE'));
  assert.throws(()=>reportsPath('','-created_at','NON_EVENT'));
});

test('Confirmation does not imply submission and workflow has precedence after sending', () => {
  const ready = reportStatus({workflow_status:'NOT_SUBMITTED',preparation_status:'READY'});
  assert.equal(ready.label,'Siap dikirim');
  assert.equal(ready.tone,'ready');
  const sent = reportStatus({workflow_status:'SUBMITTED',preparation_status:'READY'});
  assert.equal(sent.label,'Sudah dikirim');
  assert.equal(sent.tone,'sent');
  assert.equal(reportStatus({workflow_status:'CLOSED',preparation_status:'READY'}).label,'Ditutup');
  assert.equal(reportStatus({workflow_status:'NOT_SUBMITTED',preparation_status:'FAILED'}).tone,'error');
});

test('Keyword/ID search is encoded on the owner-scoped server query and retained across pages', () => {
  const url=new URL(reportsPath('SUBMITTED','-created_at','FLOOD',2,'  Jalan Melati & pasar  '),'https://silar.test/');
  assert.equal(url.searchParams.get('q'),'Jalan Melati & pasar');
  assert.equal(url.searchParams.get('scope'),'owned');
  assert.equal(url.searchParams.get('page'),'2');
  assert.equal(url.searchParams.get('event_type'),'FLOOD');
  assert.equal(new URL(reportsPath('','-created_at','',1,'   '),'https://silar.test/').searchParams.has('q'),false);
});
