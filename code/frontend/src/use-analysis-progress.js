import {computed,onBeforeUnmount,ref} from 'vue';
import {ApiError} from './api.js';
import {progressSnapshot,readAnalysisProgress,validateProgressRun} from './analysis-progress.js';
import {requiresStoredState} from './recovery.js';
export function useAnalysisProgress(request){
  const visible=ref(false),run=ref(null),target=ref(null),readError=ref(null),outcome=ref('preparing'),resultRead=ref(false);
  let epoch=0,timer,controller,alive=true;
  function stop(){epoch++;clearTimeout(timer);controller?.abort();}
  function prepare(route,mode='EVIDENCE'){if(!alive)return;stop();visible.value=true;run.value=null;target.value={route,mode};outcome.value='preparing';readError.value=null;resultRead.value=false;}
  async function poll(version){
    if(version!==epoch)return;
    const currentController=new AbortController();controller=currentController;
    try{
      const value=await readAnalysisProgress((path)=>request(path,{signal:currentController.signal}),target.value,run.value?.id);
      if(version!==epoch)return;
      readError.value=null;
      if(value){run.value=value;outcome.value=value.status==='FAILED'?'failed':value.status==='UNKNOWN'?'unknown':'running';}
    }catch(e){if(version===epoch&&e.name!=='AbortError'&&e.status!==404)readError.value=e;}
    if(version===epoch&&!['FAILED','UNKNOWN','SUCCEEDED'].includes(run.value?.status))timer=setTimeout(()=>poll(version),1200);
  }
  function start(value){if(!alive)return;stop();target.value={...target.value,...value};outcome.value='running';poll(epoch);}
  function complete(detail,response){
    const id=response?.data?.object?.id||response?.data?.result?.id;
    const value=validateProgressRun(detail?.latest_run,target.value);
    if(!id||value.id!==id||value.status!=='SUCCEEDED'||detail.report.id!==target.value.reportId||
      detail.report.active_bundle_id!==target.value.bundle_id||detail.report.input_revision!==target.value.input_revision||
      detail.current_card?.id!==detail.report.current_card_version_id||detail.current_card?.narrative_id!==value.output_narrative_id)
      throw new ApiError('Hasil analisis perlu dibaca kembali sebelum melanjutkan.','RESPONSE_UNKNOWN');
    stop();run.value=value;readError.value=null;resultRead.value=true;outcome.value='complete';
  }
  function fail(error){stop();outcome.value=requiresStoredState(error)?'unknown':'failed';readError.value=error;}
  function reset(){stop();visible.value=false;run.value=null;target.value=null;resultRead.value=false;readError.value=null;}
  const state=computed(()=>({...progressSnapshot(run.value,target.value?.route,target.value?.mode,{resultRead:resultRead.value}),visible:visible.value,outcome:outcome.value,readError:readError.value}));
  onBeforeUnmount(()=>{alive=false;stop();});
  return {state,prepare,start,complete,fail,reset};
}
