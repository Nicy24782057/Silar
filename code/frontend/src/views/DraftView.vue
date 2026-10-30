<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
import {useAnalysisProgress} from '../use-analysis-progress';
import {evidenceRoute} from '../analysis-progress';
import AnalysisProgress from '../components/AnalysisProgress.vue';
import AppDialog from '../components/AppDialog.vue';
import { useRoute, useRouter } from 'vue-router';
import { api, ApiError } from '../api';
import {reportRequests, readStoredReportAction, reportRequestGuidance, requestAction, requiresStoredState} from '../recovery';
import { online } from '../network';
import { validateText, validateFile, validateBundle, usesGemini, paginationPath, label, date, size, textLength } from '../domain';
import ErrorNotice from '../components/ErrorNotice.vue';
import AudioRecorder from '../components/AudioRecorder.vue';
import ReportReview from '../components/ReportReview.vue';
import VersionHistory from '../components/VersionHistory.vue';
import AppIcon from '../components/AppIcon.vue';
import ResponsibleReporting from '../components/ResponsibleReporting.vue';
import FetchState from '../components/FetchState.vue';
import DeleteDraftDialog from '../components/DeleteDraftDialog.vue';
const deleting=ref(false),historyOpen=ref(false),progressPanel=ref(null);
const progress=useAnalysisProgress(api);
import welcomeArt from '../assets/reference/reporter-welcome.svg';
import ReportStatus from '../components/ReportStatus.vue';
import { reportStatus } from '../report-list';
import { reportStageAccess } from '../report-flow';
import { reviewState } from '../review';
import { defaultEvidence, useSavedEvidence, sameEvidence, uploadProblem, analyseSavedEvidence } from '../evidence';
const route=useRoute();const router=useRouter();
const detail=ref(null);const evidence=ref([]);const count=ref(0);const next=ref(null);const selected=ref([]);
const text=ref('');const audio=ref(null);const images=ref([]);const preview=ref({});
const busy=ref(false);const loading=ref(false);const analysing=ref(false);const error=ref(null);const message=ref('');
const readError=ref(null),inputChannel=ref('TEXT');
let loadSequence=0,loadAbort,disposed=false;
const unknown=ref(false);const consent=ref(false);const requestRows=ref([]);
const tab=ref('input'),tabChosen=ref(false),reviewBusy=ref(false);
const editingText=ref(false),sourceChosen=ref(false);
const advancedCardId=ref(null),reviewEditing=ref(false),navigationMessage=ref('');
const savedReceipt=ref(null),evidencePanel=ref(null),receiptPanel=ref(null),inputPanel=ref(null),noticeRegion=ref(null),stageHeading=ref(null);
const requestNext=ref(null);const selectedRequest=ref(null);const recoveredRun=ref(null);const includeExpired=ref(false);
const isNew=computed(()=>route.params.id==='new');
const report=computed(()=>detail.value?.report);
const active=computed(()=>detail.value?.active_bundle);
const editable=computed(()=>report.value?.workflow_status==='NOT_SUBMITTED');
const held=computed(()=>['RUNNING','UNKNOWN'].includes(detail.value?.latest_run?.status));
const locked=computed(()=>busy.value||loading.value||analysing.value||reviewBusy.value||unknown.value||!online.value);
const selectedItems=computed(()=>{const known=new Map(evidence.value.map(x=>[x.id,x]));for(const x of active.value?.items||[])known.set(x.evidence.id,x.evidence);return selected.value.map(id=>known.get(id)).filter(Boolean);});
const selectionSaved=computed(()=>Boolean(active.value)&&sameEvidence(active.value.items,selected.value));
const selectionProblem=computed(()=>validateBundle(selectedItems.value));
const currentText=computed(()=>selectedItems.value.find(item=>item.type==='TEXT'));
const currentAudio=computed(()=>selectedItems.value.find(item=>item.type==='AUDIO'));
const archive=computed(()=>evidence.value.filter(item=>!selected.value.includes(item.id)));
const hasUnsavedInput=computed(()=>Boolean(editingText.value||text.value.trim()||audio.value||images.value.length));
const pendingInput=computed(()=>Boolean(hasUnsavedInput.value||next.value||(active.value&&!selectionSaved.value)));
const stageTitle=computed(()=>isNew.value?'Buat laporan':report.value?.submitted_at?'Detail laporan':({input:'Simpan bukti',review:'Periksa hasil',confirm:'Konfirmasi & kirim',history:'Versi & riwayat'}[tab.value]));
const stageSubtitle=computed(()=>isNew.value?'Mulai dari informasi yang Anda ketahui.':({input:'Simpan sumber asli sebelum menjalankan analisis.',review:'Bandingkan hasil analisis dengan bukti dan narasi.',confirm:'Konfirmasi versi yang tepat, lalu kirim melalui tindakan terpisah.',history:'Baca versi dan tindakan yang telah tersimpan.'}[tab.value]));
const external=computed(()=>usesGemini(selectedItems.value));
const stageAccess=computed(()=>reportStageAccess(detail.value,{pendingInput:pendingInput.value,editingReview:reviewEditing.value,advancedCardId:advancedCardId.value}));
const audioUrl=ref(null);
watch(audio, value=>{if(audioUrl.value)URL.revokeObjectURL(audioUrl.value);audioUrl.value=value?URL.createObjectURL(value):null;});
function releasePreviews(){for(const value of Object.values(preview.value))URL.revokeObjectURL(value);preview.value={};}
onBeforeUnmount(()=>{disposed=true;++loadSequence;loadAbort?.abort();releasePreviews();if(audioUrl.value)URL.revokeObjectURL(audioUrl.value);});
function addEvidence(rows){const known=new Map(evidence.value.map(x=>[x.id,x]));for(const item of rows)known.set(item.id,item);evidence.value=Array.from(known.values());}
function defaultSources(){if(!sourceChosen.value)selected.value=defaultEvidence(evidence.value,active.value).map(item=>item.id);}
function useSource(item){if(item.type==='IMAGE'&&!selected.value.includes(item.id)&&selectedItems.value.filter(row=>row.type==='IMAGE').length>=3){error.value=new ApiError('Maksimal tiga gambar aktif. Keluarkan salah satu gambar dari analisis sebelum menambahkan gambar lain.','INVALID_PAYLOAD');return;}selected.value=useSavedEvidence(selectedItems.value,item).map(row=>row.id);sourceChosen.value=true;consent.value=false;savedReceipt.value=null;}
function removeSource(item){selected.value=selected.value.filter(id=>id!==item.id);sourceChosen.value=true;consent.value=false;savedReceipt.value=null;}
function editText(){text.value=currentText.value.text_content;editingText.value=true;savedReceipt.value=null;}
function cancelText(){text.value='';editingText.value=false;}
function moveInputChannel(direction){
  const channels=['TEXT','AUDIO','IMAGE'];
  inputChannel.value=channels[(channels.indexOf(inputChannel.value)+direction+channels.length)%channels.length];
  nextTick(()=>document.getElementById('evidence-tab-'+inputChannel.value)?.focus());
}
async function focusArea(element,{alignTop=false}={}){
  await nextTick();
  if(!element?.isConnected)return;
  const box=element.getBoundingClientRect();
  if(alignTop||box.top<12||box.top>window.innerHeight-120)element.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});
  element.focus({preventScroll:true});
}
function chooseTab(value){
  if(locked.value)return false;
  if(reviewEditing.value&&value!=='review'){navigationMessage.value='Simpan atau batalkan koreksi sebelum kembali.';return false;}
  if(value==='confirm'&&tab.value!=='review')return false;
  if(value==='input')advancedCardId.value=null;
  if(value==='review'&&!stageAccess.value.review){navigationMessage.value=stageAccess.value.reviewReason;return false;}
  if(value==='confirm'&&!stageAccess.value.confirm){navigationMessage.value=stageAccess.value.confirmReason;return false;}
  const changed=tab.value!==value;
  tab.value=value;tabChosen.value=true;navigationMessage.value='';
  if(changed)nextTick(()=>focusArea(stageHeading.value));
  return true;
}
function navigateReview(value){
  if(value==='confirm'){
    const state=reviewState(detail.value);
    if(!state.current||state.nonEvent||pendingInput.value||reviewEditing.value||locked.value)return;
    advancedCardId.value=detail.value.current_card.id;
  }
  chooseTab(value);
}
watch([stageAccess,loading],()=>{
  if(loading.value||!detail.value)return;
  if(tab.value==='confirm'&&!stageAccess.value.confirm)tab.value=stageAccess.value.review?'review':'input';
  if(tab.value==='review'&&!stageAccess.value.review)tab.value='input';
});
async function viewEvidence(){await focusArea(evidencePanel.value,{alignTop:true});}
async function addMoreEvidence(){chooseTab('input');await nextTick();await focusArea(inputPanel.value,{alignTop:true});}
async function acknowledgeSaved(items,reportId){
  if(!items.length||report.value?.id!==reportId||tab.value!=='input')return;
  const label=items[0].type==='TEXT'?'Keterangan tersimpan':items[0].type==='AUDIO'?'Audio tersimpan':items.length+' gambar tersimpan';
  savedReceipt.value={ids:items.map(item=>item.id),label,partial:Boolean(error.value)};
  await nextTick();await focusArea(evidencePanel.value,{alignTop:true});receiptPanel.value?.focus({preventScroll:true});
}
function applyReviewedDetail(value){
  if(value?.report?.id!==route.params.id||route.path!=='/reports/'+value.report.id)return;
  const justSubmitted=!detail.value?.report.submitted_at&&value.report.submitted_at;
  detail.value=value;unknown.value=false;
  if(justSubmitted)router.replace('/reports/'+value.report.id+'/sent');
  if(value.report.submitted_at){releasePreviews();evidence.value=(value.official_bundle?.items||[]).map(x=>x.evidence);count.value=evidence.value.length;next.value=null;selected.value=evidence.value.map(x=>x.id);}
}
async function load(){
  const generation=++loadSequence,requestedId=route.params.id;
  loadAbort?.abort();loadAbort=new AbortController();
  error.value=null;readError.value=null;loading.value=true;requestRows.value=[];requestNext.value=null;selectedRequest.value=null;recoveredRun.value=null;releasePreviews();consent.value=false;
  if(detail.value?.report.id!==requestedId){detail.value=null;evidence.value=[];selected.value=[];count.value=0;next.value=null;}
  try{
    if(isNew.value){detail.value=null;evidence.value=[];selected.value=[];return;}
    const value=(await api('reports/'+requestedId+'/',{signal:loadAbort.signal})).data;
    if(generation!==loadSequence)return;
    if(value?.report?.id!==requestedId)throw new ApiError('Rincian tidak sesuai dengan laporan yang dipilih. Silakan coba lagi.','INVALID_RESPONSE');
    const result=value.report.workflow_status==='NOT_SUBMITTED'?await api('reports/'+requestedId+'/evidence/',{signal:loadAbort.signal}):null;
    if(generation!==loadSequence)return;
    detail.value=value;
    sourceChosen.value=false;selected.value=(detail.value.active_bundle?.items||[]).map(x=>x.evidence.id);
    evidence.value=[];count.value=0;next.value=null;
    if(editable.value){evidence.value=result.results;count.value=result.count;next.value=result.next;defaultSources();}
    else{evidence.value=(detail.value.official_bundle?.items||detail.value.active_bundle?.items||[]).map(x=>x.evidence);count.value=evidence.value.length;}
    unknown.value=false;
    if(!tabChosen.value)tab.value=stageAccess.value.confirm?'confirm':stageAccess.value.review?'review':'input';
  }catch(e){if(generation===loadSequence&&e.name!=='AbortError')readError.value=e;}finally{if(generation===loadSequence)loading.value=false;}
}
watch(()=>route.params.id,()=>{progress.reset();historyOpen.value=false;text.value='';editingText.value=false;audio.value=null;images.value=[];inputChannel.value='TEXT';message.value='';savedReceipt.value=null;advancedCardId.value=null;reviewEditing.value=false;navigationMessage.value='';tabChosen.value=false;tab.value='input';load();},{immediate:true});
async function create(){busy.value=true;error.value=null;try{const result=await api('reports/',{method:'POST',body:{},key:crypto.randomUUID()});await router.replace('/reports/'+result.data.report.id);}catch(e){fail(e);}finally{busy.value=false;}}
function fail(e){error.value=e;if(requiresStoredState(e))unknown.value=true;}
async function readEvidencePage(){const result=await api(paginationPath(next.value));addEvidence(result.results);count.value=result.count;next.value=result.next;defaultSources();}
async function more(){loading.value=true;error.value=null;try{await readEvidencePage();}catch(e){fail(e);}finally{loading.value=false;}}
async function upload(kind,value){
  if(next.value)throw new ApiError('Baca semua bukti tersimpan terlebih dahulu agar sumber analisis lengkap.','INVALID_PAYLOAD');
  const problem=kind==='TEXT'?validateText(value):validateFile(value,kind);
  if(problem)throw new ApiError(problem,'INVALID_PAYLOAD');
  const capacity=uploadProblem(selectedItems.value,kind,[value]);
  if(capacity)throw new ApiError(capacity,'INVALID_PAYLOAD');
  if(kind==='IMAGE'&&window.createImageBitmap){let bitmap;try{bitmap=await createImageBitmap(value);if(bitmap.width*bitmap.height>12_000_000)throw new ApiError('Gambar maksimal 12 megapiksel.','INVALID_PAYLOAD');}finally{bitmap?.close();}}
  const body=new FormData();body.append('type',kind);body.append('expected_revision',String(report.value.revision));
  body.append(kind==='TEXT'?'text_content':'file',value);
  const result=await api('reports/'+report.value.id+'/evidence/',{method:'POST',body,key:crypto.randomUUID()});
  detail.value.report=result.data.report;addEvidence([result.data.object]);count.value++;useSource(result.data.object);return result.data.object;
}
async function saveText(){
  const saved=[],reportId=report.value.id;
  busy.value=true;error.value=null;message.value='';savedReceipt.value=null;
  try{
    if(currentText.value?.text_content===text.value){message.value='Keterangan sama dengan versi tersimpan.';return;}
    saved.push(await upload('TEXT',text.value));text.value='';editingText.value=false;
  }catch(e){fail(e);}finally{busy.value=false;if(saved.length)await acknowledgeSaved(saved,reportId);else if(error.value||message.value)await focusArea(noticeRegion.value);}
}
async function saveAudio(event){
  const saved=[],reportId=report.value.id;
  busy.value=true;error.value=null;message.value='';savedReceipt.value=null;
  try{saved.push(await upload('AUDIO',audio.value));audio.value=null;event.target.reset();}
  catch(e){fail(e);}finally{busy.value=false;if(saved.length)await acknowledgeSaved(saved,reportId);else if(error.value)await focusArea(noticeRegion.value);}
}
async function saveImages(event){
  const saved=[],reportId=report.value.id;
  busy.value=true;error.value=null;message.value='';savedReceipt.value=null;
  try{
    if(!images.value.length)throw new ApiError('Pilih gambar terlebih dahulu.','INVALID_PAYLOAD');
    const problem=uploadProblem(selectedItems.value,'IMAGE',images.value)||images.value.map(file=>validateFile(file,'IMAGE')).find(Boolean);
    if(problem)throw new ApiError(problem,'INVALID_PAYLOAD');
    for(const file of images.value)saved.push(await upload('IMAGE',file));
  }catch(e){fail(e);}finally{busy.value=false;images.value=[];event.target.reset();if(saved.length)await acknowledgeSaved(saved,reportId);else if(error.value)await focusArea(noticeRegion.value);}
}
async function showMedia(item){
  error.value=null;if(preview.value[item.id])return;
  try{const blob=await api('evidence/'+item.id+'/media/',{raw:true});preview.value={...preview.value,[item.id]:URL.createObjectURL(blob)};}
  catch(e){fail(e);}
}
async function analyse(){
  const requestedReportId=report.value?.id;
  error.value=null;message.value='';savedReceipt.value=null;
  if(editingText.value||text.value.trim()||audio.value||images.value.length){error.value=new ApiError('Masih ada input yang belum disimpan. Simpan bukti atau kosongkan input sebelum analisis.','INVALID_PAYLOAD');return;}
  analysing.value=true;
  let showResults=false;
  try{
    if(next.value){while(next.value)await readEvidencePage();consent.value=false;message.value='Semua bukti sudah dibaca. Periksa bukti aktif dan informasi pemrosesan sebelum menekan Analisis laporan.';return;}
    tabChosen.value=true;
    const previousRunId=detail.value.latest_run?.id;
    progress.prepare(evidenceRoute(selectedItems.value));
    await nextTick();await focusArea(progressPanel.value,{alignTop:true});
    const response=await analyseSavedEvidence(api,detail.value,selectedItems.value,consent.value,value=>{detail.value=value;},target=>progress.start({...target,previousRunId}));
    if(disposed||route.params.id!==requestedReportId)return;
    await load();
    if(disposed||route.params.id!==requestedReportId)return;
    if(readError.value)throw new ApiError('Hasil analisis perlu dibaca kembali sebelum melanjutkan.','RESPONSE_UNKNOWN');
    progress.complete(detail.value,response);showResults=true;message.value='Analisis selesai. Periksa hasil dan bandingkan dengan sumber. Laporan belum dikirim.';
  }catch(e){if(e.status===404||e.status===405)e=new ApiError('Layanan analisis belum tersedia. Bukti dan bundle tetap tersimpan; coba kembali setelah layanan siap.','AI_CONFIGURATION_NOT_READY',503);fail(e);if(progress.state.value.visible)progress.fail(e);await focusArea(noticeRegion.value);}
  finally{analysing.value=false;}
  if(showResults&&!disposed&&route.params.id===requestedReportId)chooseTab('review');
}
async function checkRequests(){
  loading.value=true;error.value=null;
  try{await load();loading.value=true;const result=await api('requests/?report_id='+route.params.id+'&include_expired='+includeExpired.value);requestRows.value=reportRequests(result.results,route.params.id);requestNext.value=result.next;
    if(!requestRows.value.length)message.value=requestNext.value?'Belum ada permintaan pada halaman ini. Muat riwayat berikutnya untuk mencari tindakan terdahulu.':'Tidak ada permintaan yang sesuai. Periksa sumber dan hasil tersimpan sebelum tindakan baru.';
  }catch(e){if(e.status===404)e=new ApiError('Pembacaan request analisis belum tersedia. Bukti dapat diperiksa melalui daftar sumber tersimpan.','AI_CONFIGURATION_NOT_READY',503);fail(e);}finally{loading.value=false;}
}
async function moreRequests(){
  loading.value=true;error.value=null;
  try{const result=await api(paginationPath(requestNext.value));const rows=reportRequests(result.results,route.params.id);
    requestRows.value=[...new Map([...requestRows.value,...rows].map(item=>[item.key,item])).values()];requestNext.value=result.next;
  }catch(e){fail(e);}finally{loading.value=false;}
}
async function readRequest(key){
  loading.value=true;error.value=null;message.value='';selectedRequest.value=null;recoveredRun.value=null;
  try{const result=await readStoredReportAction(api,route.params.id,key);applyReviewedDetail(result.detail);selectedRequest.value=result.request;recoveredRun.value=result.run;unknown.value=false;
    message.value=reportRequestGuidance(result.request);
  }catch(e){fail(e);}finally{loading.value=false;}
}
</script>
<template>
 <div class="compose-page">
  <div class="page-heading report-page-heading"><div><div class="eyebrow">RUANG REPORTER</div><h1 ref="stageHeading" tabindex="-1">{{ stageTitle }}</h1><p class="subtitle">{{ stageSubtitle }}</p></div><RouterLink class="report-back-link" to="/reports"><AppIcon name="left" :size="15" />Daftar laporan</RouterLink></div>
  <div ref="noticeRegion" class="report-notices" tabindex="-1"><ErrorNotice :error="error" /><div v-if="message" class="notice success" role="status">{{ message }}</div></div>
  <div v-if="unknown" class="notice warning">Hasil tindakan terakhir belum pasti. Baca kembali draft dan periksa bukti tersimpan sebelum mengulang.<button class="small" :disabled="locked" @click="load">Baca draft tersimpan</button></div>
  <template v-if="isNew">
   <section class="draft-start-banner">
    <div class="draft-start-copy"><h2>Siapkan laporan Anda</h2><p>Mulai dari informasi yang Anda ketahui. Simpan bukti,<br class="draft-desktop-break"> periksa hasil, lalu konfirmasi sebelum mengirim.</p><button :disabled="locked" @click="create"><AppIcon name="plus" :size="17" />{{ busy?'Membuat draft…':'Buat draft' }}</button><div class="draft-start-channels"><span><AppIcon name="file" :size="16" />Teks</span><span><AppIcon name="audio" :size="16" />Audio</span><span><AppIcon name="image" :size="16" />Foto</span></div><small>Gunakan salah satu kanal atau kombinasinya.</small></div>
    <img :src="welcomeArt" alt="" class="draft-start-art">
   </section>
   <div class="draft-start-grid"><div><h2 class="flow-heading">Alur laporan</h2><div class="flow-grid"><section v-for="([icon,title,description],index) in [['file','Simpan bukti','Simpan minimal satu kanal asli yang valid sebelum analisis.'],['search','Periksa hasil','Bandingkan Incident Card dan narasi dengan sumber.'],['send','Konfirmasi & kirim','Konfirmasi versi yang tepat, lalu kirim secara terpisah.']]" :key="title" class="card flow-card"><div><span>0{{ index+1 }}</span><AppIcon :name="icon" :size="20" /></div><h3>{{ title }}</h3><p>{{ description }}</p></section></div><section class="draft-coverage"><h3>Cakupan kejadian</h3><div><span v-for="[icon,title] in [['waves','Banjir'],['pulse','Gempa bumi'],['flame','Kebakaran'],['car','Kecelakaan']]" :key="title"><AppIcon :name="icon" :size="18" />{{ title }}</span></div></section><p class="draft-storage-note"><AppIcon name="info" :size="16" />Draft dan bukti tersimpan secara online. Gunakan sumber yang berhak Anda gunakan.</p></div><aside class="support-stack" aria-label="Panduan pelaporan"><ResponsibleReporting /><section class="draft-privacy"><h3><AppIcon name="lock" :size="17" />Laporan tetap privat</h3><p>Pengiriman kepada Operator belum berarti laporan diterbitkan ke Portal Publik.</p></section></aside></div>
  </template>
  <FetchState v-else-if="loading&&!detail" title="Memuat rincian laporan…" description="Membaca draft, bukti, dan versi laporan yang dipilih." :caption="'#'+route.params.id.slice(0,8)" />
  <FetchState v-if="readError" state="error" title="Rincian laporan belum dapat dimuat" description="Coba lagi untuk membaca sumber dan keadaan terbaru. Kegagalan pembacaan berbeda dari status Analisis gagal pada laporan." :caption="'#'+route.params.id.slice(0,8)" :error="readError" :disabled="locked" @retry="load" />
  <template v-if="detail&&!isNew">
   <div class="report-meta" :aria-busy="loading"><strong>#{{ report.id.slice(0,8) }}</strong><ReportStatus v-if="!analysing" :status="reportStatus(report)" /><span v-else class="badge">Analisis berlangsung</span><span class="badge">{{ report.submitted_at?'Sudah dikirim':'Belum dikirim' }}</span><span class="badge">{{ selectedItems.length }} bukti {{ editable?'aktif':'resmi' }}</span><span class="report-meta-version">{{ detail.current_card?'Incident Card · v'+detail.current_card.version_number:'Kartu belum tersedia' }}</span><div class="report-meta-actions"><button v-if="editable" class="report-delete-button" aria-label="Hapus laporan" :disabled="locked" @click="deleting=true">Hapus</button><button :aria-expanded="historyOpen" aria-haspopup="dialog" :disabled="locked" @click="historyOpen=true"><AppIcon name="history" :size="16" />Versi & riwayat</button><button :disabled="locked" @click="load"><AppIcon name="refresh" :size="16" :class="{'is-spinning':loading}" />{{ loading?'Memuat…':'Muat ulang' }}</button></div></div>
   <div v-if="editable" class="report-navigation"><ol class="report-stepper" aria-label="Tahapan laporan"><li v-for="([value,title,caption],index) in [['input','Simpan bukti','Input & sumber analisis'],['review','Periksa hasil','Bandingkan & koreksi'],['confirm','Konfirmasi & kirim','Dua tindakan terpisah']]" :key="value"><div class="report-step" :aria-current="tab===value?'step':undefined" :class="{active:tab===value,complete:['input','review','confirm'].indexOf(tab)>index,unavailable:value!=='input'&&!stageAccess[value]}"><span class="step-number" :class="{complete:['input','review','confirm'].indexOf(tab)>index}"><AppIcon v-if="['input','review','confirm'].indexOf(tab)>index" name="check" :size="15" /><template v-else>{{ index+1 }}</template></span><span class="step-label"><strong>{{ title }}</strong><small>{{ caption }}</small></span><AppIcon v-if="value!=='input'&&!stageAccess[value]" class="step-lock" name="lock" :size="12" /></div></li></ol><p id="report-flow-help" class="report-flow-help">{{ navigationMessage||(tab==='confirm'?'Konfirmasi versi yang diperiksa, lalu kirim laporan.':tab==='review'?'Periksa hasil, lalu gunakan tombol Lanjut atau Kembali.':'Simpan bukti dan jalankan analisis. Hasil akan terbuka otomatis setelah selesai.') }}</p></div>
   <nav v-else class="report-readonly-tabs" aria-label="Bagian laporan resmi"><button v-for="[value,title] in [['input','Bukti'],['review','Hasil dan narasi'],['confirm','Versi resmi']]" :key="value" :aria-current="tab===value?'page':undefined" :disabled="locked" @click="tab=value">{{ title }}</button></nav>
   <div v-if="tab==='input'" ref="progressPanel" tabindex="-1"><AnalysisProgress :state="progress.state.value" /></div>
   <div v-if="!editable&&tab==='input'" class="notice">Laporan sudah dikirim dan sumbernya terkunci. Bukti serta hasil tetap dapat dibaca sesuai hak akses.</div>
   <div v-show="tab==='input'" class="draft-grid">
    <div v-if="editable" class="draft-input-column"><section ref="inputPanel" class="card input-panel" tabindex="-1" aria-label="Formulir informasi dan bukti"><header class="compose-panel-heading"><h2>Tambahkan bukti</h2><p>Semua bukti aktif digunakan bersama. Anda dapat memakai beberapa kanal.</p></header><div class="compose-panel-body">
     <div class="compose-tabs" role="tablist" aria-label="Kanal bukti"><button v-for="[value,title,icon] in [['TEXT','Teks','file'],['AUDIO','Audio','audio'],['IMAGE','Foto','image']]" :id="'evidence-tab-'+value" :key="value" type="button" role="tab" :aria-selected="inputChannel===value" :aria-controls="'evidence-input-'+value" :tabindex="inputChannel===value?0:-1" @click="inputChannel=value" @keydown.right.prevent="moveInputChannel(1)" @keydown.left.prevent="moveInputChannel(-1)"><AppIcon :name="icon" :size="16" />{{ title }}</button></div>
     <p v-if="next" class="notice warning">Baca semua bukti tersimpan dahulu melalui tombol di panel bukti agar sumber laporan lengkap.</p>
     <form v-show="inputChannel==='TEXT'" id="evidence-input-TEXT" role="tabpanel" aria-labelledby="evidence-tab-TEXT" method="post" action="#" @submit.prevent="saveText"><fieldset :disabled="locked||Boolean(next)"><div class="compose-field-title"><label for="incident-text">Keterangan kejadian</label><span class="badge" :class="{'evidence-unsaved':editingText||text.trim()}">{{ editingText||text.trim()?'Belum disimpan':currentText?'Tersimpan':'Belum diisi' }}</span></div><template v-if="currentText&&!editingText"><p class="evidence-text compose-saved-text">{{ currentText.text_content }}</p><p class="fine">Satu keterangan aktif digunakan untuk analisis. Perubahan menyimpan versi baru; teks sebelumnya tetap tersimpan.</p><button class="secondary" type="button" @click="editText"><AppIcon name="edit" :size="16" />Ubah keterangan</button></template><template v-else><textarea id="incident-text" v-model="text" name="text_content" rows="5" aria-describedby="text-help" placeholder="Ceritakan kejadian yang Anda ketahui…" required></textarea><div id="text-help" class="field-help"><span>Jangan menambahkan informasi yang belum diketahui.</span><span>{{ textLength(text) }} / 5.000</span></div><div class="review-actions"><button class="primary" type="submit" :disabled="!text.trim()"><AppIcon name="check" :size="16" />{{ editingText?'Simpan perubahan keterangan':'Simpan bukti teks' }}</button><button v-if="editingText" type="button" @click="cancelText">Batal ubah keterangan</button></div></template></fieldset></form>
     <form v-show="inputChannel==='AUDIO'" id="evidence-input-AUDIO" role="tabpanel" aria-labelledby="evidence-tab-AUDIO" method="post" action="#" @submit.prevent="saveAudio"><fieldset :disabled="locked||Boolean(next)"><div class="compose-field-title"><label for="audio-file">Rekaman suara</label><span v-if="audio" class="badge evidence-unsaved">Belum disimpan</span></div><p v-if="currentAudio" class="fine">Audio aktif: {{ currentAudio.original_name }}. Audio baru menggantikan sumber aktif; rekaman sebelumnya tetap tersimpan di arsip.</p><div class="compose-upload"><AppIcon name="audio" :size="27" /><strong>Unggah satu audio atau rekam langsung</strong><input id="audio-file" name="audio" type="file" accept=".wav,.mp3,.m4a,.mp4,.webm,audio/wav,audio/mpeg,audio/mp4,audio/webm" @change="audio=$event.target.files[0]||null"><small>WAV PCM, MP3, WebM/Opus, atau M4A/MP4-AAC tanpa video dan cover gambar · maksimal 10 MiB dan dua menit.</small></div><AudioRecorder :disabled="locked||Boolean(next)" @recorded="audio=$event"/><p v-if="audio" class="file-name">{{ audio.name }} · {{ size(audio.size) }}</p><audio v-if="audioUrl" :src="audioUrl" controls preload="metadata" aria-label="Dengarkan rekaman sebelum disimpan"></audio><button class="primary" type="submit" :disabled="!audio"><AppIcon name="check" :size="16" />{{ currentAudio?'Simpan pengganti audio':'Simpan bukti audio' }}</button></fieldset></form>
     <form v-show="inputChannel==='IMAGE'" id="evidence-input-IMAGE" role="tabpanel" aria-labelledby="evidence-tab-IMAGE" method="post" action="#" @submit.prevent="saveImages"><fieldset :disabled="locked||Boolean(next)"><div class="compose-field-title"><label for="image-files">Foto kejadian</label><span v-if="images.length" class="badge evidence-unsaved">Belum disimpan</span></div><div class="compose-upload"><AppIcon name="image" :size="28" /><strong>Pilih foto kejadian</strong><input id="image-files" name="images" type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg" multiple @change="images=Array.from($event.target.files)"><small>PNG atau JPEG · maksimal 5 MiB dan 12 megapiksel per foto; maksimal tiga foto aktif.</small></div><ul v-if="images.length" class="pending-files"><li v-for="file in images" :key="file.name">{{ file.name }} · {{ size(file.size) }}</li></ul><button class="primary" type="submit" :disabled="!images.length"><AppIcon name="check" :size="16" />Simpan bukti gambar</button></fieldset></form>
    </div></section><section class="draft-privacy"><h3><AppIcon name="lock" :size="17" />Simpan setiap bukti sebelum analisis.</h3><p>Bukti asli dan versi sebelumnya tetap tersedia pada sumber tersimpan.</p></section></div>
    <aside class="support-stack" aria-label="Bukti dan analisis"><section ref="evidencePanel" class="card sources-panel" tabindex="-1" aria-labelledby="active-evidence-heading"><header class="compose-panel-heading"><h2 id="active-evidence-heading">{{ editable?'Bukti aktif untuk analisis':'Bukti resmi' }}</h2><span class="badge">{{ selectedItems.length }} bukti {{ editable?'aktif':'resmi' }}</span></header><div class="compose-panel-body">
     <div v-if="savedReceipt" ref="receiptPanel" class="evidence-receipt" :class="{partial:savedReceipt.partial}" tabindex="-1" role="status"><strong><AppIcon name="check" :size="17" />{{ savedReceipt.label }}</strong><p>{{ savedReceipt.partial?'Sebagian unggahan belum berhasil. Bukti yang sudah tersimpan ditandai di bawah.':'Bukti yang baru disimpan ditandai di bawah dan otomatis dipakai untuk analisis berikutnya.' }}</p><p v-if="savedReceipt.partial&&error">{{ error.message }}</p></div>
     <div v-if="!selectedItems.length" class="compose-evidence-empty"><span><AppIcon name="reports" :size="26" /></span><h3>Belum ada bukti tersimpan</h3><p>Simpan teks, audio, atau foto terlebih dahulu.</p></div>
     <ul v-else class="evidence-list"><li v-for="item in selectedItems" :key="item.id" :data-evidence-id="item.id" class="evidence-item" :class="{'just-saved':savedReceipt?.ids.includes(item.id)}"><div class="evidence-top"><AppIcon :name="item.type==='TEXT'?'file':item.type==='AUDIO'?'audio':'image'" :size="18" /><strong>{{ item.type==='TEXT'?'Teks asli':item.original_name }}</strong><span class="badge">Privat</span></div><p v-if="item.type==='TEXT'" class="evidence-text">{{ item.text_content }}</p><span v-if="savedReceipt?.ids.includes(item.id)" class="evidence-new-label"><AppIcon name="check" :size="12" />Baru disimpan</span><div class="evidence-meta">{{ size(item.byte_size) }} · {{ date(item.created_at) }}</div><template v-if="item.type!=='TEXT'"><button class="link" :disabled="!online" @click="showMedia(item)"><AppIcon :name="item.type==='IMAGE'?'image':'audio'" :size="15" />{{ preview[item.id]?'Media telah dibuka':item.type==='IMAGE'?'Buka gambar privat':'Dengarkan audio privat' }}</button><img v-if="preview[item.id]&&item.type==='IMAGE'" class="evidence-image" :src="preview[item.id]" :alt="'Bukti gambar: '+item.original_name"><audio v-if="preview[item.id]&&item.type==='AUDIO'" :src="preview[item.id]" controls preload="metadata" :aria-label="'Bukti audio: '+item.original_name"></audio></template><button v-if="editable&&item.type==='IMAGE'" class="link" :disabled="locked||Boolean(next)" @click="removeSource(item)">Keluarkan gambar dari analisis</button></li></ul>
     <p class="compose-evidence-note">Bukti aktif dapat digabungkan antar kanal.</p>
     <template v-if="editable"><details v-if="archive.length" class="evidence-archive"><summary>Arsip bukti sebelumnya ({{ archive.length }})</summary><p class="fine">Menggunakan teks atau audio lama menggantikan kanal aktif yang sama. Sumber baru diterapkan saat Analisis laporan ditekan.</p><ul class="evidence-list"><li v-for="item in archive" :key="item.id" class="evidence-item"><strong>{{ item.type==='TEXT'?'Keterangan sebelumnya':item.original_name }}</strong><p v-if="item.type==='TEXT'" class="evidence-text">{{ item.text_content }}</p><div class="evidence-meta">{{ size(item.byte_size) }} · {{ date(item.created_at) }}</div><button :disabled="locked||editingText||Boolean(next)" class="small" @click="useSource(item)">{{ item.type==='TEXT'?'Gunakan keterangan ini':item.type==='AUDIO'?'Gunakan audio ini':'Gunakan gambar ini' }}</button></li></ul></details><p v-if="next" class="fine">{{ evidence.length }} dari {{ count }} bukti tersimpan telah dibaca.</p><button v-if="next" class="full" :disabled="locked" @click="more">Muat bukti berikutnya</button></template>
    </div></section><section v-if="editable" class="card compose-analysis"><h2><AppIcon name="shield" :size="21" />Analisis laporan</h2><p>Maksimal satu teks, satu audio, dan tiga foto; total bukti 25 MiB.</p><p v-if="selectionProblem&&selectedItems.length" class="notice warning">{{ selectionProblem }}</p><p v-if="external" class="fine">Rute ini memakai Gemini: teks, transkrip, atau gambar yang relevan diproses layanan AI eksternal. Audio asli diproses lokal; data akun dan kredensial tidak dikirim.</p><p v-else-if="selectedItems.length" class="fine">Kanal tunggal teks atau audio diproses melalui jalur lokal tanpa Gemini.</p><label v-if="external&&!next" class="check-label consent"><input v-model="consent" type="checkbox" :disabled="locked">Saya telah membaca informasi pemrosesan eksternal.</label><button class="primary full" :disabled="locked||held||(!next&&Boolean(selectionProblem||hasUnsavedInput))" @click="analyse"><AppIcon name="arrow" :size="16" />{{ analysing?'Memproses…':next?'Baca semua bukti sebelum analisis':'Analisis laporan' }}</button><p class="fine">{{ hasUnsavedInput?'Simpan atau kosongkan isian yang belum disimpan sebelum analisis.':!selectedItems.length?'Simpan minimal satu bukti dan selesaikan isian yang belum disimpan sebelum analisis.':'Setelah analisis, periksa hasil sebelum melanjutkan ke konfirmasi.' }}</p><p v-if="held" class="fine">{{ label(detail.latest_run.status) }}. Analisis baru ditahan sampai keadaan proses dipastikan.</p><p v-if="active&&!selectionSaved" class="fine">Bukti aktif berubah. Hasil sebelumnya tetap memiliki sumber lamanya; sumber baru disimpan saat analisis berikutnya.</p></section></aside>
   </div>
   <div v-if="editable&&tab==='input'" class="section-actions report-flow-actions"><p>{{ analysing?'Analisis sedang berjalan. Tunggu hasil tersimpan sebelum melanjutkan.':stageAccess.review?'Hasil tersedia. Lanjutkan untuk membandingkan dengan bukti.':'Selesaikan analisis untuk membuka tahap Periksa hasil.' }}</p><button class="primary" :disabled="locked||!stageAccess.review" @click="chooseTab('review')">Lanjut ke periksa hasil<AppIcon name="arrow" :size="15" /></button></div>
   <ReportReview :key="report.id" v-show="tab==='review'||tab==='confirm'" :stage="tab" :detail="detail" :disabled="locked" :pending-input="pendingInput" @updated="applyReviewedDetail" @working="reviewBusy=$event" @navigate="navigateReview" @editing="reviewEditing=$event" />
   <AppDialog v-if="historyOpen" title="Versi & riwayat" :caption="'Laporan #'+report.id.slice(0,8)" @close="historyOpen=false"><VersionHistory :report-id="report.id" /><template #actions><button @click="historyOpen=false">Tutup</button></template></AppDialog>
   <details class="request-recovery" :open="unknown||held"><summary><AppIcon name="history" :size="21" /><span><strong>Riwayat analisis & pemulihan</strong><small>Periksa keadaan tersimpan jika hasil belum muncul atau koneksi terputus.</small></span><AppIcon name="down" :size="17" /></summary><div class="request-recovery-body"><button :disabled="busy||analysing||loading||reviewBusy||!online" @click="checkRequests"><AppIcon name="refresh" :size="16" />Periksa permintaan dan hasil tersimpan</button><label class="check-label"><input v-model="includeExpired" type="checkbox" :disabled="loading||analysing||reviewBusy">Sertakan riwayat permintaan yang lebih lama</label><div v-if="requestRows.length||requestNext" class="card"><h2>Permintaan tersimpan</h2><p class="muted">Baca keadaan analisis, koreksi, konfirmasi atau pengiriman tanpa menjalankan tindakan ulang.</p><ul class="request-list"><li v-for="item in requestRows" :key="item.key"><strong>{{ requestAction(item.scope) }} · {{ label(item.state) }}</strong> · {{ date(item.created_at) }}<small v-if="item.error_code">{{ item.error_code }}</small><button class="small" :disabled="busy||analysing||loading||reviewBusy||!online" @click="readRequest(item.key)">Baca permintaan ini</button></li></ul><button v-if="requestNext" class="full" :disabled="busy||analysing||loading||reviewBusy||!online" @click="moreRequests">Muat riwayat berikutnya</button></div><div v-if="selectedRequest" class="card" role="status"><h2>Keadaan permintaan yang dipilih</h2><p><strong>{{ requestAction(selectedRequest.scope) }} · {{ label(selectedRequest.state) }}</strong> · {{ date(selectedRequest.created_at) }}</p><p>{{ reportRequestGuidance(selectedRequest) }}</p><p v-if="selectedRequest.error_code">Kode hasil: {{ selectedRequest.error_code }}</p><p v-if="recoveredRun">Tahap terakhir: {{ label(recoveredRun.stage) }} · {{ label(recoveredRun.status) }}</p><p class="fine">Tampilan laporan mengikuti sumber dan versi terbaru.</p></div></div></details>
  </template>
  <DeleteDraftDialog v-if="deleting&&report" :report="report" @close="deleting=false" @deleted="deleting=false;router.replace('/reports')" @refresh="load" />
 </div>
</template>
