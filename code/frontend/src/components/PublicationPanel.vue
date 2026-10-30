<script setup>
import {computed,onBeforeUnmount,reactive,ref,watch} from 'vue';
import {api,ApiError} from '../api';
import {session} from '../session';
import {online} from '../network';
import {date,label,paginationPath} from '../domain';
import {handlerCan,workspaceLabel} from '../workspace';
import {publicProjection} from '../publication';
import {canDraftPublication,publicationValues,publicationReceipt,publicationRequest,reviewedPublicationCandidate} from '../operator-flow';
import {requiresStoredState} from '../recovery';
import AppDialog from './AppDialog.vue';
import AppIcon from './AppIcon.vue';
import PublicIncidentCard from './PublicIncidentCard.vue';
import WorkspaceStatus from './WorkspaceStatus.vue';
import ErrorNotice from './ErrorNotice.vue';
import ProcessOutlet from './ProcessOutlet.vue';
const props=defineProps({detail:{type:Object,required:true},blocked:Boolean,start:Boolean,decisionReason:{type:String,default:''}});
const emit=defineEmits(['saved','busy']);
const data=ref(null),versions=ref([]),latest=ref(null),busy=ref(false),saving=ref(false),error=ref(null),message=ref('');
const editor=ref(false),sanitized=ref(false),preview=ref(null),confirmation=ref(null),confirmed=ref(false),reason=ref('');
const unknown=ref(null),missingRequest=ref(false),activePacket=ref(null),savingLabel=ref(''),draftBase=ref(null),startConsumed=ref(false);
const form=reactive({summary:'',general_location:'',time_text:'',occurred_at:'',general_impact:'',handling_update:''});
let sequence=0,alive=true,controller;
const reportId=computed(()=>props.detail.report.id);
const candidate=computed(()=>data.value?.active_candidate);
const published=computed(()=>data.value?.published_version);
const allowed=computed(()=>handlerCan(session.user,props.detail,'publish_report')&&data.value?.assignment?.operator_id===session.user?.id);
const disabled=computed(()=>!online.value||busy.value||saving.value||props.blocked||Boolean(unknown.value));
const canCreate=computed(()=>allowed.value&&canDraftPublication(data.value));
const needsDecision=computed(()=>data.value?.report.publication_status!=='PENDING_APPROVAL');
const viewKey=computed(()=>candidate.value?candidate.value.state+':'+candidate.value.id:editor.value?'editor':published.value?'published':'start');
const formPreview=computed(()=>{
 const validTime=/(Z|[+-]\d{2}:\d{2})$/i.test(form.occurred_at)&&Number.isFinite(Date.parse(form.occurred_at));
 return publicProjection({data:{event_type:data.value?.official_card?.data?.event_type,...form,occurred_at:validTime?form.occurred_at:null},published_at:null},reportId.value);
});
async function load({clearError=true}={}){
 const generation=++sequence,id=reportId.value;controller?.abort();const requestController=new AbortController();controller=requestController;
 const read=path=>api(path,{signal:requestController.signal});busy.value=true;if(clearError)error.value=null;
 try{
  const result=await read(`reports/${id}/`);if(generation!==sequence)return null;
  if(result.data?.report?.id!==id)throw new ApiError('Rincian publikasi tidak sesuai laporan.','INVALID_RESPONSE');
  const rows=[];let path=`reports/${id}/versions/?kind=PublicationVersion&page_size=100`;
  while(path){const page=await read(path);if(generation!==sequence)return null;rows.push(...page.results);path=page.next?paginationPath(page.next):null;}
  rows.sort((a,b)=>b.version_number-a.version_number);
  let previous=null;
  if(rows.length&&props.detail.private_access){
   const result=await read(`reports/${id}/versions/PublicationVersion/${rows[0].id}/`);if(generation!==sequence)return null;
   previous=result.data.version;
  }
  data.value=result.data;versions.value=rows;latest.value=previous;
  if(candidate.value||!canCreate.value)editor.value=false;
  else if(props.start&&!startConsumed.value&&!editor.value&&!unknown.value)edit();
  return result.data;
 }catch(e){if(generation===sequence&&e.name!=='AbortError'){if([401,403,404].includes(e.status))data.value=null;error.value=e;}return null;}
 finally{if(generation===sequence)busy.value=false;}
}
function edit(){
 if(!canCreate.value)return;
 const card=data.value.official_card,previous=latest.value?.data;
 const source=previous||{summary:card.narrative?.text?.slice(0,2000)||data.value.active_narrative?.text?.slice(0,2000)||'',general_location:card.data.location_text,time_text:card.data.time_text,occurred_at:card.data.occurred_at,general_impact:(card.data.impacts||[]).join('; ').slice(0,2000),handling_update:null};
 for(const key of Object.keys(form))form[key]=source[key]??'';
 draftBase.value={revision:data.value.report.revision,parentId:latest.value?.id??null};
 sanitized.value=false;editor.value=true;startConsumed.value=true;error.value=null;message.value='';
}
function packet(action,body,versionId=null){
 const id=reportId.value,part=action==='decision'?'publication-decision':action==='create'?'publication-versions':`publication-versions/${versionId}/${action}`;
 return {reportId:id,key:crypto.randomUUID(),action,versionId,path:`reports/${id}/${part}/`,
  scope:`publication.${action}${versionId?':'+versionId:''}:${id}`,body:{...body,expected_revision:data.value.report.revision}};
}
async function step(target){
 activePacket.value=target;
 const response=publicationReceipt(await api(target.path,{method:'POST',key:target.key,body:target.body}),target);
 if(!alive||target.reportId!==reportId.value)return null;
 savingLabel.value='Membaca hasil tersimpan…';
 if(!await load({clearError:false}))throw new ApiError('Hasil tindakan perlu dibaca kembali sebelum melanjutkan.','RESPONSE_UNKNOWN');
 if(!alive||target.reportId!==reportId.value)return null;
 return response;
}
async function task(work){
 if(disabled.value)return;saving.value=true;emit('busy',true);error.value=null;message.value='';missingRequest.value=false;
 const id=reportId.value;
 try{
  await work();if(!alive||id!==reportId.value)return;
  const action=activePacket.value?.action;unknown.value=null;activePacket.value=null;confirmed.value=false;confirmation.value=null;emit('saved',{action});
 }catch(e){
  if(!alive||id!==reportId.value)return;
  if(requiresStoredState(e)&&activePacket.value)unknown.value=activePacket.value;
  await load({clearError:false});error.value=e;emit('saved');
 }finally{if(alive){saving.value=false;savingLabel.value='';emit('busy',false);}}
}
async function create(){
 if(disabled.value||!canCreate.value||!sanitized.value)return;
 let values;
 try{values=publicationValues(form);}catch(e){error.value=e;return;}
 if(needsDecision.value&&!props.decisionReason.trim()){error.value=new ApiError('Isi alasan keputusan publikasi di atas sebelum melanjutkan.','INVALID_PAYLOAD');return;}
 if(draftBase.value?.revision!==data.value.report.revision){error.value=new ApiError('Keadaan laporan berubah. Baca ulang sumber sebelum menyimpan isi publik.','VERSION_CONFLICT');return;}
 const parentId=draftBase.value.parentId,decisionReason=props.decisionReason.trim(),category=data.value.official_card.data.event_type;
 await task(async()=>{
  if(needsDecision.value){
   savingLabel.value='Menyimpan keputusan publikasi…';
   const result=await step(packet('decision',{decision:'PREPARE',reason:decisionReason}));if(!result)return;
   draftBase.value={revision:data.value.report.revision,parentId};
   if(data.value.report.revision!==result.report.revision||!canCreate.value||data.value.report.publication_status!=='PENDING_APPROVAL'||(latest.value?.id??null)!==parentId)
    throw new ApiError('Keadaan publikasi berubah. Periksa kembali sebelum menyimpan isi publik.','VERSION_CONFLICT');
  }
  savingLabel.value='Menyimpan isi publikasi…';
  const result=await step(packet('create',{parent_id:parentId,data:values}));if(!result)return;
  if(candidate.value?.id!==result.object.id)throw new ApiError('Versi tersimpan perlu dipastikan.','RESPONSE_UNKNOWN');
  const version=reviewedPublicationCandidate(data.value,result.object.id,values,category);
  savingLabel.value='Mengonfirmasi isi publikasi…';
  if(!await step(packet('approve',{},version.id)))return;
  editor.value=false;confirmed.value=false;message.value='Isi publikasi sudah disimpan dan dikonfirmasi sesuai pratinjau yang Anda periksa. Laporan belum terbit. Tekan Publikasikan sekarang untuk menerbitkannya.';
 });
}
function askCancel(){confirmation.value={version:candidate.value,revision:data.value.report.revision};reason.value='';error.value=null;}
async function confirmCandidate(action){
 if(disabled.value||!allowed.value||!candidate.value||!confirmed.value)return;
 const version=candidate.value,expected=action==='approve'?'DRAFT':'APPROVED';
 if(version.state!==expected)return;
 const target=packet(action,{},version.id);
 await task(async()=>{
  savingLabel.value=action==='approve'?'Mengonfirmasi isi publikasi…':'Menerbitkan publikasi…';
  if(!await step(target))return;
  message.value=action==='approve'?'Isi publikasi sudah dikonfirmasi. Periksa versi ini sekali lagi, lalu tekan Publikasikan sekarang. Laporan belum terbit.':'Publikasi berhasil diterbitkan. Informasi ini sekarang dapat dibaca di Portal Publik.';
 });
}
async function cancelCandidate(){
 if(disabled.value||!confirmation.value||!reason.value.trim())return;
 const target=confirmation.value;
 if(candidate.value?.id!==target.version.id||data.value.report.revision!==target.revision){error.value=new ApiError('Versi publikasi berubah. Buka kembali pembatalan.','VERSION_CONFLICT');return;}
 await task(async()=>{savingLabel.value='Membatalkan draf publikasi…';if(await step(packet('cancel',{reason:reason.value.trim()},target.version.id)))message.value='Draf publikasi sudah dibatalkan. Anda dapat memperbaiki isi dan meninjaunya kembali.';});
}
async function recover(){
 const target=unknown.value;if(!target||saving.value||busy.value||!online.value)return;
 saving.value=true;emit('busy',true);error.value=null;missingRequest.value=false;
 try{
  const record=publicationRequest((await api(`requests/${target.key}/`)).data,target);
  if(!alive||target.reportId!==reportId.value)return;
  if(!['SUCCEEDED','FAILED'].includes(record.state)){message.value='Tindakan masih diproses atau belum pasti. Baca kembali sebelum melanjutkan.';return;}
  if(!await load({clearError:false}))return;
  unknown.value=null;activePacket.value=null;confirmation.value=null;confirmed.value=false;
  if(record.state==='SUCCEEDED'){
   if(editor.value&&!candidate.value)draftBase.value={revision:data.value.report.revision,parentId:latest.value?.id??null};
   message.value=target.action==='publish'?'Publikasi telah tersimpan. Keadaan terbit sudah dibaca kembali.':'Tindakan sudah tersimpan. Lanjutkan dari keadaan publikasi yang ditampilkan.';
  }else message.value='Tindakan gagal dan sudah tercatat. Periksa isian sebelum mencoba kembali.';
  emit('saved',{action:target.action});
 }catch(e){if(alive){error.value=e;if(e.status===404)missingRequest.value=true;}}
 finally{if(alive){saving.value=false;emit('busy',false);}}
}
async function replay(){
 const target=unknown.value;if(!target||!missingRequest.value||saving.value)return;
 // Only explicit recovery reuses the frozen key/body. It never starts the next step.
 saving.value=true;emit('busy',true);error.value=null;
 try{await step(target);if(!alive)return;unknown.value=null;activePacket.value=null;missingRequest.value=false;confirmed.value=false;confirmation.value=null;message.value='Keadaan tindakan sudah dipulihkan. Periksa hasil sebelum melanjutkan.';emit('saved',{action:target.action});}
 catch(e){if(alive)error.value=e;}finally{if(alive){saving.value=false;emit('busy',false);}}
}
async function openVersion(item){
 const generation=sequence,id=reportId.value;error.value=null;
 try{const result=await api(`reports/${id}/versions/PublicationVersion/${item.id}/`);if(generation!==sequence||id!==reportId.value)return;const version=result.data.version;preview.value=version.data?publicProjection(version,id):version;}
 catch(e){if(generation===sequence)error.value=e;}
}
watch(()=>props.start,value=>{startConsumed.value=false;if(value&&!busy.value&&!saving.value&&!unknown.value&&!editor.value)edit();});
watch(()=>props.detail.report.revision,revision=>{if(!saving.value&&data.value?.report.revision!==revision)load({clearError:false});});
watch(reportId,()=>{startConsumed.value=false;editor.value=false;unknown.value=null;confirmation.value=null;preview.value=null;data.value=null;message.value='';load();},{immediate:true});
watch(()=>candidate.value?.id+':'+candidate.value?.state,()=>{confirmed.value=false;});
onBeforeUnmount(()=>{alive=false;++sequence;controller?.abort();emit('busy',false);});
</script>
<template>
 <section class="card publication-panel publication-guided" aria-labelledby="publication-panel-title" :aria-busy="busy||saving">
  <header class="section-heading"><div><p class="eyebrow">PUBLIKASI</p><h2 id="publication-panel-title">Informasi untuk Portal Publik</h2><p class="muted">Periksa pratinjau, konfirmasi isi, lalu publikasikan.</p></div><button :disabled="busy||saving||!online" @click="load"><AppIcon name="refresh" :size="15" />Muat ulang</button></header>
  <ErrorNotice :error="error" />
  <p v-if="saving" class="publication-progress" role="status"><AppIcon name="refresh" class="is-spinning" :size="17" />{{ savingLabel||'Menyimpan…' }}</p>
  <p v-else-if="busy" role="status">Membaca versi publikasi…</p>
  <p v-if="message" class="notice success" role="status">{{ message }}</p>
  <div v-if="unknown" class="notice warning" role="status"><strong>Hasil tindakan belum pasti.</strong> Periksa hasil tersimpan sebelum melanjutkan.<button :disabled="saving||busy||!online" @click="recover">Periksa hasil tindakan</button><p v-if="missingRequest">Rekam permintaan belum ditemukan. Pulihkan dengan kunci dan isi yang sama.</p><button v-if="missingRequest" :disabled="saving||busy||!online" @click="replay">Pulihkan permintaan yang sama</button></div>
  <template v-if="data">
   <p v-if="published" class="notice success">{{ published.version_number?'Versi '+published.version_number+' telah terbit.':'Informasi laporan telah terbit.' }} {{ candidate||editor?'Versi ini tetap tampil sampai penggantinya diterbitkan.':'Informasi dapat dibaca di Portal Publik.' }}</p>
   <p v-else class="fine">Laporan belum diterbitkan di Portal Publik.</p>
   <p v-if="!allowed" class="fine">{{ detail.report.workflow_status==='CLOSED'?'Laporan sudah ditutup. Perubahan publikasi dikunci.':'Publikasi dikelola penanggung jawab saat ini yang memiliki izin publikasi.' }}</p>
   <ProcessOutlet :view-key="viewKey" label="Tahapan publikasi">
    <section v-if="candidate" class="publication-version publication-preview-step">
     <header><div><h3 data-process-heading>{{ candidate.state==='APPROVED'?'Pratinjau terkonfirmasi':'Periksa pratinjau publikasi' }}</h3><small>Versi {{ candidate.version_number }} · {{ date(candidate.created_at) }}</small></div><WorkspaceStatus :value="candidate.state" /></header>
     <PublicIncidentCard :record="publicProjection(candidate,reportId)" preview />
     <p class="fine">Pratinjau ini adalah isi publik versi tersimpan. Bukti privat dan data akun tidak ditampilkan di portal.</p>
     <template v-if="allowed">
      <label class="check-label"><input v-model="confirmed" type="checkbox" :disabled="disabled"><span>{{ candidate.state==='DRAFT'?'Saya sudah memeriksa pratinjau dan memastikan informasi ini layak untuk publik.':'Saya memastikan versi tersimpan ini adalah informasi yang akan diterbitkan.' }}</span></label>
      <div class="actions"><button class="primary" :disabled="disabled||!confirmed" @click="confirmCandidate(candidate.state==='DRAFT'?'approve':'publish')">{{ candidate.state==='DRAFT'?'Konfirmasi isi publikasi':'Publikasikan sekarang' }}<AppIcon :name="candidate.state==='DRAFT'?'check':'globe'" :size="16" /></button><button class="danger" :disabled="disabled" @click="askCancel">Batalkan draf publikasi</button></div>
     </template>
    </section>
    <form v-else-if="editor&&canCreate" class="publication-editor" @submit.prevent="create">
     <h3 data-process-heading>Periksa isi dan pratinjau publikasi</h3><p class="fine">Isi awal mengikuti {{ latest?'versi publikasi terakhir':'sumber resmi' }}. Hapus identitas, kontak, alamat terperinci, dan informasi privat. Kategori tetap {{ label(data.official_card.data.event_type) }}.</p>
     <div class="publication-edit-grid"><div class="publication-fields"><div class="field wide"><label for="public-summary">Ringkasan kejadian *</label><textarea id="public-summary" v-model="form.summary" required maxlength="2000" :disabled="disabled" /></div><div class="field"><label for="public-location">Lokasi umum</label><input id="public-location" v-model="form.general_location" maxlength="500" :disabled="disabled"></div><div class="field"><label for="public-time">Waktu yang disebut</label><input id="public-time" v-model="form.time_text" maxlength="300" :disabled="disabled"></div><div class="field wide"><label for="public-occurred">Waktu pasti (jika diketahui)</label><input id="public-occurred" v-model="form.occurred_at" placeholder="2026-10-30T15:00:00+07:00" aria-describedby="public-time-note" :disabled="disabled"><small id="public-time-note">Sertakan zona waktu. Kosongkan jika belum diketahui.</small></div><div class="field"><label for="public-impact">Dampak umum</label><textarea id="public-impact" v-model="form.general_impact" maxlength="2000" :disabled="disabled" /></div><div class="field"><label for="public-handling">Perkembangan penanganan</label><textarea id="public-handling" v-model="form.handling_update" maxlength="2000" :disabled="disabled" /></div></div>
     <section class="publication-live-preview"><h3>Pratinjau untuk publik</h3><PublicIncidentCard :record="formPreview" preview /><p class="fine">Pratinjau mengikuti isian formulir. Informasi ini belum diterbitkan.</p></section></div>
     <label class="check-label"><input v-model="sanitized" type="checkbox" :disabled="disabled"><span>Saya telah memeriksa sumber, sanitasi informasi pribadi, dan kelayakan isi untuk publik.</span></label>
     <p v-if="needsDecision&&!decisionReason.trim()" class="fine">Isi alasan keputusan di atas untuk melanjutkan.</p>
     <div class="actions"><button class="primary" :disabled="disabled||!sanitized||!form.summary.trim()||(needsDecision&&!decisionReason.trim())">Konfirmasi isi publikasi<AppIcon name="check" :size="16" /></button><button type="button" :disabled="disabled" @click="edit">Baca ulang sumber</button></div>
     <p class="fine">Konfirmasi menyimpan dan menyetujui isi yang Anda periksa. Setelah itu, tekan Publikasikan sekarang. Laporan belum terbit hanya dengan konfirmasi.</p>
    </form>
    <div v-else-if="published" class="publication-complete"><AppIcon name="circle-check" :size="34" /><h3 data-process-heading>Informasi sudah tersedia untuk publik</h3><div class="actions"><button :disabled="disabled" @click="preview=publicProjection(published,reportId)">Lihat informasi terbit</button><RouterLink class="button primary" to="/public">Buka Portal Publik<AppIcon name="arrow" :size="15" /></RouterLink></div><button v-if="canCreate&&start" :disabled="disabled" @click="edit">Perbaiki isi publikasi</button><p v-else-if="canCreate" class="fine">Untuk memperbarui informasi, pilih Tinjau untuk publikasi pada bagian Keputusan.</p></div>
    <div v-else><p class="fine">{{ canCreate?'Pilih Tinjau untuk publikasi pada bagian Keputusan. Isi dan pratinjau akan langsung ditampilkan.':'Publikasi memerlukan review Valid terhadap versi resmi.' }}</p><button v-if="canCreate&&start" :disabled="disabled" @click="edit">Perbaiki isi publikasi</button></div>
   </ProcessOutlet>
   <details class="publication-history"><summary>Riwayat versi publikasi ({{ versions.length }})</summary><p v-if="!versions.length" class="muted">Belum ada versi publikasi.</p><div v-if="versions.length" class="ws-table-scroll"><table class="ws-table"><thead><tr><th>Versi</th><th>Dibuat</th><th>Keadaan saat ini</th><th>Rincian</th></tr></thead><tbody><tr v-for="item in versions" :key="item.id"><td>Versi {{ item.version_number }}</td><td>{{ date(item.created_at) }}</td><td>{{ item.id===candidate?.id?workspaceLabel(candidate.state):item.official?'Tampil di Portal Publik':'Versi terdahulu' }}</td><td><button class="link" :disabled="disabled" @click="openVersion(item)">Pratinjau versi</button></td></tr></tbody></table></div></details>
  </template>
  <AppDialog v-if="preview" title="Pratinjau Incident Card publik" @close="preview=null"><PublicIncidentCard :record="preview" preview /><template #actions><button @click="preview=null">Tutup pratinjau</button></template></AppDialog>
  <AppDialog v-if="confirmation" title="Batalkan draf publikasi?" :caption="'VERSI '+confirmation.version.version_number" @close="!saving&&(confirmation=null)"><p>{{ published?'Versi terbit lama tetap tersedia.':'Informasi ini belum terbit.' }} Draf yang dibatalkan tetap tersimpan dalam riwayat.</p><div class="field"><label for="cancel-publication-reason">Alasan pembatalan *</label><textarea id="cancel-publication-reason" v-model="reason" required maxlength="3000" :disabled="saving" /></div><template #actions><button :disabled="saving" @click="confirmation=null">Kembali</button><button class="danger" :disabled="disabled||!reason.trim()" @click="cancelCandidate">Batalkan draf publikasi</button></template></AppDialog>
 </section>
</template>
