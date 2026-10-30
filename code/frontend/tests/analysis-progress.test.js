import test from 'node:test';
import assert from 'node:assert/strict';
import {analysisSteps,evidenceRoute,progressSnapshot,readAnalysisProgress} from '../src/analysis-progress.js';
const target={reportId:'report',key:'key',bundle_id:'bundle',input_revision:3,mode:'EVIDENCE',route:'TAI',previousRunId:'old'};
const run={id:'run',report_id:'report',bundle_id:'bundle',input_revision:3,mode:'EVIDENCE',route:'TAI',stage:'NARA',status:'RUNNING',timings_ms:{NARRATIVE:10,SENA:20}};
const record={key:'key',report_id:'report',scope:'POST reports/report/analyses/',state:'RUNNING',result_id:null,result_type:null};
test('Seven evidence routes and revised narratives use only the stages actually executed',()=>{
 for(const route of ['T','A','I','TA','TI','AI','TAI']){
  assert.equal(analysisSteps(route).some(x=>x.key==='WHISPER'),route.includes('A'));
  assert.equal(analysisSteps(route,'NARRATIVE_REVISION').some(x=>x.key==='WHISPER'),false);
 }
 assert.equal(evidenceRoute([{type:'IMAGE'},{type:'TEXT'},{type:'AUDIO'}]),'TAI');
});
test('Progress stays at zero without server evidence and counts completed stages, not elapsed time',()=>{
 assert.equal(progressSnapshot(null,'T').percent,0);
 const started=progressSnapshot(run);assert.equal(started.completed,4);assert.equal(started.percent,50);
 const completed=progressSnapshot({...run,timings_ms:{...run.timings_ms,NARA:0}});
 assert.equal(completed.completed,5);assert.equal(completed.percent,62);
 assert.equal(progressSnapshot(run).percent,started.percent);
});
test('100 percent requires both a succeeded run and a completed read of its stored result',()=>{
 const saved={...run,status:'SUCCEEDED',stage:'PERSIST'};
 assert.equal(progressSnapshot(saved).percent,87);
 assert.equal(progressSnapshot(saved,null,null,{resultRead:true}).percent,100);
 for(const status of ['RUNNING','UNKNOWN','FAILED'])assert(progressSnapshot({...saved,status},null,null,{resultRead:true}).percent<100);
});
test('An earlier run is never shown as the newly requested analysis',async()=>{
 const calls=[];
 const result=await readAnalysisProgress(async path=>{calls.push(path);return {data:path.startsWith('requests/')?record:{report:{id:'report'},latest_run:{...run,id:'old',status:'SUCCEEDED'}}};},target);
 assert.equal(result,null);assert(calls.every(p=>!p.includes('analyses/')));
});
test('The request and report scope must match before a running analysis can be bound',async()=>{
 await assert.rejects(readAnalysisProgress(async()=>({data:{...record,key:'another'}}),target),e=>e.code==='INVALID_RESPONSE');
 await assert.rejects(readAnalysisProgress(async()=>({data:{...record,report_id:'another'}}),target),e=>e.code==='INVALID_RESPONSE');
});
test('A reservation is rechecked before binding the report latest run',async()=>{
 const calls=[];const result=await readAnalysisProgress(async path=>{calls.push(path);return {data:path.startsWith('requests/')?record:{report:{id:'report'},latest_run:run}};},target);
 assert.equal(result.id,'run');assert.equal(calls.filter(p=>p.startsWith('requests/')).length,2);
});
test('A concurrent later run cannot replace the result linked by the original request',async()=>{
 let reads=0;
 const linked={...run,id:'original',status:'SUCCEEDED'};
 const result=await readAnalysisProgress(async path=>({data:path.startsWith('requests/')?(++reads===1?record:{...record,state:'SUCCEEDED',result_type:'Run',result_id:'original'}):path.includes('analysis-runs/')?linked:{report:{id:'report'},latest_run:run}}),target);
 assert.equal(result.id,'original');
});
test('Bound runs with the wrong source, mode or report are rejected',async()=>{
 for(const bad of [{report_id:'other'},{bundle_id:'older'},{input_revision:2},{mode:'NARRATIVE_REVISION'},{route:'T'}]){
  await assert.rejects(readAnalysisProgress(async()=>({data:{...run,...bad}}),target,'run'),e=>e.code==='INVALID_RESPONSE');
 }
});
