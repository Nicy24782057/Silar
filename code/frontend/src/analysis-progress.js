import {ApiError} from './api.js';
export const evidenceRoute = items => ['TEXT','AUDIO','IMAGE'].filter(type=>items.some(item=>item.type===type)).map(type=>({TEXT:'T',AUDIO:'A',IMAGE:'I'}[type])).join('');
export function analysisSteps(route,mode='EVIDENCE') {
  return [
    ['INPUT','Memeriksa sumber'],
    ...(mode==='EVIDENCE'&&route?.includes('A')?[['WHISPER','Mengubah audio menjadi teks']]:[]),
    ['NARRATIVE','Menyusun narasi'],['SENA','Mengenali kategori dengan SENA'],
    ['NARA','Mengurai informasi dengan NARA'],['FUSION','Menyatukan hasil analisis'],
    ['PERSIST','Menyimpan hasil'],['READ','Membaca hasil tersimpan'],
  ].map(([key,label])=>({key,label}));
}
export function progressSnapshot(run,route,mode,{resultRead=false}={}) {
  const steps=analysisSteps(run?.route||route,run?.mode||mode);
  let completed=0;
  if(run){
    const index=steps.findIndex(step=>step.key===run.stage);
    completed=Math.max(0,index);
    if(index>=0&&Number.isFinite(run.timings_ms?.[run.stage]))completed=Math.max(completed,index+1);
    // A committed run proves persistence; the final client read is separate.
    if(run.status==='SUCCEEDED')completed=steps.length-1;
    if(resultRead&&run.status==='SUCCEEDED')completed=steps.length;
  }
  return {steps:steps.map((step,index)=>({...step,state:index<completed?'done':index===completed?'current':'waiting'})),
    completed,total:steps.length,percent:Math.floor(completed/steps.length*100),
    label:completed===steps.length?'Hasil siap diperiksa':steps[completed]?.label||'Memeriksa hasil'};
}
const invalid=()=>new ApiError('Referensi progres tidak sesuai dengan analisis ini.','INVALID_RESPONSE');
export function validateProgressRun(run,target) {
  if(!run?.id||!['T','A','I','TA','TI','AI','TAI'].includes(run.route)||(target.route&&run.route!==target.route)||run.report_id!==target.reportId||run.bundle_id!==target.bundle_id||
    run.input_revision!==target.input_revision||run.mode!==target.mode||
    (target.mode==='NARRATIVE_REVISION'&&run.input_narrative_id!==target.narrative_id))throw invalid();
  return run;
}
function validateRecord(record,target){
  if(record?.key!==target.key||record.report_id!==target.reportId||record.scope!==`POST reports/${target.reportId}/analyses/`)throw invalid();
  return record;
}
export async function readAnalysisProgress(read,target,runId=null) {
  if(runId)return validateProgressRun((await read(`reports/${target.reportId}/analysis-runs/${runId}/`)).data,target);
  const record=validateRecord((await read(`requests/${target.key}/`)).data,target);
  if(record.result_type==='Run'&&record.result_id)return readAnalysisProgress(read,target,record.result_id);
  if(!['RUNNING','UNKNOWN'].includes(record.state))return null;
  const detail=(await read(`reports/${target.reportId}/`)).data;
  if(detail?.report?.id!==target.reportId)throw invalid();
  const run=detail.latest_run;
  if(!run||run.id===target.previousRunId)return null;
  validateProgressRun(run,target);
  // While a ledger is active, there can only be one active run on this report.
  // Re-read it to exclude a different run that started between our two reads.
  const after=validateRecord((await read(`requests/${target.key}/`)).data,target);
  if(after.result_type==='Run'&&after.result_id!==run.id)return readAnalysisProgress(read,target,after.result_id);
  if(!['RUNNING','UNKNOWN'].includes(after.state)&&after.result_id!==run.id)return null;
  return run;
}
