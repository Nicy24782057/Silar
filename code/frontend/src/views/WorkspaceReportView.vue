<script setup>
import {computed,nextTick,onBeforeUnmount,reactive,ref,watch} from 'vue';
import {useRoute} from 'vue-router';
import {api,ApiError} from '../api';
import {session} from '../session';
import {date,label} from '../domain';
import {online} from '../network';
import {requiresStoredState} from '../recovery';
import {fieldLabels} from '../analysis';
import {hasPermission,handlerCan,closeAllowed,decisionAllowed,shortId,workspaceLabel,eventLabels,roleLabel,reportTabLocked,adminReportsScope,ADMIN_REPORTS_PATH} from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
import FetchState from '../components/FetchState.vue';
import WorkspaceStatus from '../components/WorkspaceStatus.vue';
import WorkspaceAssignment from '../components/WorkspaceAssignment.vue';
import WorkspaceEvidence from '../components/WorkspaceEvidence.vue';
import PublicationPanel from '../components/PublicationPanel.vue';
import WorkspaceAi from '../components/WorkspaceAi.vue';
import ProcessOutlet from '../components/ProcessOutlet.vue';
import {savedReview} from '../operator-flow';
const route=useRoute();
const detail=ref(null),busy=ref(false),saving=ref(false),error=ref(null),message=ref(''),tab=ref('summary');
const assignment=ref(false),closing=ref(false),finish=ref(null);
const uncertain=ref(false),publicationSaving=ref(false),technical=ref(false),pendingAction=ref(null),missingAction=ref(false);
const historyRows=computed(()=>(detail.value?.history||[]).filter(item=>technical.value||!/^(ANALYSIS_|EVIDENCE_|BUNDLE_|NARRATIVE_|CARD_|REPORT_CREATED|HUMAN_VERIFIED)/.test(item.action)));
const mutationBlocked=computed(()=>saving.value||busy.value||uncertain.value||publicationSaving.value||Boolean(readError.value));
const reviewReceipt=ref(null),tabNavigation=ref(null);
watch(tab,async()=>{await nextTick();const nav=tabNavigation.value,button=nav?.querySelector('[aria-current="page"]');if(!button)return;const a=button.getBoundingClientRect(),n=nav.getBoundingClientRect();if(a.left<n.left||a.right>n.right)nav.scrollBy({left:a.left-n.left-(n.width-a.width)/2,behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});});
const review=reactive({outcome:'',reason:''}),followup=ref(''),decision=reactive({decision:'',reason:''}),closure=ref(''),finishReason=ref('');
const closed=computed(()=>detail.value?.report?.workflow_status==='CLOSED');
const privateAccess=computed(()=>detail.value?.private_access===true);
const tabs=computed(()=>[
 ['summary',privateAccess.value?'Ringkasan':'Ringkasan Monitoring'],
 ...(privateAccess.value?[['evidence','Bukti'],['ai','Narasi & AI']]:[]),
 ['review','Review'],['followup','Tindak Lanjut'],['decision','Keputusan'],['history','Riwayat']
]);
const canAssign=computed(()=>session.user?.role==='ADMIN'&&hasPermission(session.user,'assign_report')&&!closed.value&&!uncertain.value);
const reviewOpen=computed(()=>handlerCan(session.user,detail.value,'review_report')&&!detail.value.has_active_candidate&&!detail.value.report.published_version_id&&!['APPROVED','PUBLISHED'].includes(detail.value.report.publication_status));
const back=computed(()=>adminReportsScope(session.user)?ADMIN_REPORTS_PATH:'/workspace/assigned');
function show(value){if(value===null||value===undefined||value==='')return 'Belum tersedia';if(Array.isArray(value))return value.length?value.map(v=>typeof v==='object'?JSON.stringify(v):v).join('; '):'Belum tersedia';return typeof value==='object'?JSON.stringify(value):String(value);}
const readError=ref(null);
let generation=0;
async function load({quiet=false}={}){
 const version=++generation,id=route.params.id;readError.value=null;
 if(!quiet){busy.value=true;error.value=null;}
 try{
  const r=await api(`workspace/reports/${id}/`);if(version!==generation)return null;
  if(r.data?.report?.id!==id)throw new ApiError('Rincian tidak sesuai dengan laporan yang dipilih.','INVALID_RESPONSE');
  detail.value=r.data;
  if(!decision.decision&&r.data.report.publication_status==='PENDING_APPROVAL'&&!r.data.has_active_candidate){decision.decision='PREPARE';decision.reason=r.data.decision_reason||'';}
  if(!tabs.value.some(x=>x[0]===tab.value))tab.value='summary';
  else if(reportTabLocked(detail.value,tab.value))tab.value='review';
  return r.data;
 }catch(e){
  if(version===generation){
   if(!quiet||[401,403,404].includes(e.status)){detail.value=null;assignment.value=false;closing.value=false;finish.value=null;}
   readError.value=e;
  }
  return null;
 }finally{if(version===generation)busy.value=false;}
}
function changeTab(value){if(saving.value||publicationSaving.value||reportTabLocked(detail.value,value))return;if(tab.value!==value)message.value='';tab.value=value;}
function advanceReview(packet){
 const stored=savedReview(detail.value,packet);
 if(!stored)throw new ApiError('Review perlu dibaca kembali sebelum melanjutkan.','RESPONSE_UNKNOWN');
 reviewReceipt.value=stored;review.outcome='';review.reason='';tab.value='followup';
 message.value='Review resmi berhasil disimpan. Lanjutkan penanganan laporan.';
}
async function write(action,body){
 if(mutationBlocked.value||!detail.value)return false;
 const packet={id:detail.value.report.id,key:crypto.randomUUID(),action,body:{...body,expected_revision:detail.value.report.revision},...(action==='reviews'?{reviewContext:{previousIds:detail.value.reviews.map(item=>item.id),cardId:detail.value.report.official_card_version_id,operatorId:session.user.id}}:{})};
 return perform(packet);
}
async function perform(packet){
 saving.value=true;error.value=null;message.value='';
 try{
  const r=await api(`workspace/reports/${packet.id}/${packet.action}/`,{method:'POST',key:packet.key,body:packet.body});
  if(route.params.id!==packet.id)return false;
  if(r.data?.report?.id!==packet.id)throw new ApiError('Respons tindakan perlu dipastikan.','RESPONSE_UNKNOWN');
  if(!await load({quiet:true}))throw new ApiError('Tindakan perlu dibaca kembali sebelum melanjutkan.','RESPONSE_UNKNOWN');
  if(route.params.id!==packet.id)return false;
  pendingAction.value=null;uncertain.value=false;missingAction.value=false;
  message.value=r.data.message||'Tindakan berhasil disimpan.';
  if(packet.action==='reviews')advanceReview(packet);
  return true;
 }catch(e){
  if(route.params.id!==packet.id)return false;
  await load({quiet:true});error.value=e;
  if(requiresStoredState(e)){pendingAction.value=packet;uncertain.value=true;closing.value=false;finish.value=null;tab.value='history';}
  else{pendingAction.value=null;uncertain.value=false;}
  return false;
 }finally{saving.value=false;}
}
async function recoverAction(){
 const packet=pendingAction.value;if(!packet||saving.value)return;saving.value=true;error.value=null;missingAction.value=false;
 try{
  const record=(await api(`requests/${packet.key}/`)).data;
  if(route.params.id!==packet.id)return;
  if(record?.key!==packet.key||record.report_id!==packet.id)throw new ApiError('Referensi tindakan tidak sesuai laporan.','INVALID_RESPONSE');
  if(['SUCCEEDED','FAILED'].includes(record.state)){
   if(!await load({quiet:true}))throw new ApiError('Keadaan laporan belum dapat dibaca kembali.','NETWORK_ERROR');
   if(route.params.id!==packet.id)return;
   if(record.state==='SUCCEEDED'&&packet.action==='reviews')advanceReview(packet);
   else message.value=record.state==='SUCCEEDED'?'Tindakan telah tersimpan. Keadaan laporan sudah dibaca kembali.':'Kegagalan tindakan telah tercatat. Periksa keadaan laporan sebelum mencoba kembali.';
   pendingAction.value=null;uncertain.value=false;
  }else message.value='Hasil tindakan masih diproses atau belum pasti. Tindakan baru tetap ditahan.';
 }catch(e){error.value=e;if(e.status===404)missingAction.value=true;}finally{saving.value=false;}
}
async function saveReview(){if(!review.outcome)return;if(await write('reviews',{outcome:review.outcome,reason:review.reason.trim()})){review.reason='';review.outcome='';}}
async function saveFollowup(){if(!reportTabLocked(detail.value,'followup')&&await write('followups',{description:followup.value.trim()}))followup.value='';}
async function saveDecision(){if(decision.decision==='INTERNAL'&&!reportTabLocked(detail.value,'decision')&&await write('decision',{decision:decision.decision,reason:decision.reason.trim()}))decision.reason='';}
async function close(){if(await write('close',{closure_note:closure.value.trim()})){closing.value=false;closure.value='';}}
function finishing(item,status){finish.value={...item,nextStatus:status};finishReason.value='';}
async function saveFinish(){if(await write(`followups/${finish.value.id}`,{status:finish.value.nextStatus,completion_reason:finishReason.value.trim()}))finish.value=null;}
async function publicationSaved(event){message.value='';if(event?.action==='publish'){decision.decision='';decision.reason='';}await load({quiet:true});}
async function assigned(text){assignment.value=false;message.value=text;await load({quiet:true});}
watch(()=>route.params.id,()=>{detail.value=null;tab.value='summary';message.value='';uncertain.value=false;pendingAction.value=null;missingAction.value=false;technical.value=false;review.outcome='';review.reason='';reviewReceipt.value=null;followup.value='';decision.decision='';decision.reason='';load();},{immediate:true});
onBeforeUnmount(()=>{generation+=1;detail.value=null;});
</script>
<template>
 <div class="page-heading ws-page-heading"><div><div class="eyebrow">PENANGANAN SAYA / DETAIL LAPORAN</div><h1>{{ privateAccess?'Detail Laporan':'Ringkasan Laporan' }}</h1><p class="subtitle">{{ shortId(route.params.id) }}<template v-if="detail"> · Versi resmi {{ detail.report.official_version }} · {{ label(detail.report.event_type) }}</template></p></div><div class="ws-reference-heading-actions"><RouterLink class="button" :to="back"><AppIcon name="left" :size="15" />Kembali</RouterLink><button :disabled="busy||saving||publicationSaving" @click="load({quiet:Boolean(detail)})"><AppIcon name="refresh" :size="15" />Muat ulang</button></div></div>
 <ErrorNotice :error="error" /><FetchState v-if="busy" title="Memuat rincian laporan…" :caption="shortId(route.params.id)" description="Membaca versi resmi dan keadaan penanganan terbaru." /><FetchState v-else-if="readError" state="error" title="Rincian laporan belum dapat dimuat" :caption="shortId(route.params.id)" description="Coba lagi untuk membaca laporan yang dipilih." :error="readError" :disabled="busy||saving||publicationSaving" @retry="load()" /><p v-if="message" class="notice success" role="status">{{ message }}</p>
 <div v-if="uncertain" class="notice warning" role="status">Respons tindakan terputus. Periksa hasil tersimpan sebelum melakukan tindakan berikutnya. Tindakan baru ditahan sampai hasilnya diketahui.<button :disabled="saving||!online" @click="recoverAction">Periksa hasil tindakan</button><p v-if="missingAction">Rekam permintaan belum dapat ditemukan. Anda dapat memulihkan tindakan dengan kunci dan isi permintaan yang sama.</p><button v-if="missingAction&&pendingAction" :disabled="saving||!online" @click="perform(pendingAction)">Kirim ulang permintaan yang sama</button></div>
 <template v-if="detail">
  <section class="ws-report-reference-banner" :data-category="detail.report.event_type"><div class="ws-reference-category"><span><AppIcon :name="detail.report.event_type==='FLOOD'?'waves':detail.report.event_type==='FIRE'?'flame':detail.report.event_type==='ACCIDENT'?'car':'pulse'" :size="26" /></span><div><small>LAPORAN RESMI</small><h2>{{ label(detail.report.event_type) }}</h2></div><p>Dikirim {{ date(detail.report.submitted_at) }}</p></div><div><small>Penanggung jawab</small><strong>{{ detail.assignment?.operator_name||'Belum ditugaskan' }}</strong><small>Penanganan</small><WorkspaceStatus :value="detail.report.workflow_status" /></div><div><small>Review</small><WorkspaceStatus :value="detail.report.validation_status" /><p>Versi resmi {{ detail.report.official_version }}</p></div><div><small>Publikasi</small><WorkspaceStatus :value="detail.report.publication_status" /><p>Ruang penanganan privat</p></div></section>
  <div v-if="canAssign" class="ws-reference-assignment"><button :disabled="busy||saving||publicationSaving" @click="assignment=true">{{ detail.assignment?'Alihkan petugas':'Tugaskan laporan' }}</button></div>
  <p v-if="closed" class="notice success"><AppIcon name="lock" :size="17" />Laporan ditutup pada {{ date(detail.report.closed_at) }}. Perubahan laporan dan penugasan telah dikunci; pembacaan tetap mengikuti hak akses.</p>
  <p v-else-if="!privateAccess" class="ws-info-line"><AppIcon name="shield" :size="18" />Ringkasan administratif. Bukti, narasi, dan hasil AI privat hanya dapat dibaca penanggung jawab saat ini yang memiliki izin.</p>
  <nav ref="tabNavigation" class="ws-tabs" aria-label="Bagian laporan"><button v-for="[key,title] in tabs" :key="key" :class="{active:tab===key}" :disabled="saving||publicationSaving||reportTabLocked(detail,key)" :aria-describedby="reportTabLocked(detail,key)?'review-step-hint':undefined" :title="reportTabLocked(detail,key)?'Catat dan simpan review resmi terlebih dahulu.':undefined" :aria-current="tab===key?'page':undefined" aria-controls="workspace-process-body" @click="changeTab(key)"><AppIcon v-if="reportTabLocked(detail,key)" name="lock" :size="14" />{{ title }}</button></nav>
  <div v-if="reportTabLocked(detail,'followup')" id="review-step-hint" class="ws-stage-hint"><AppIcon name="info" :size="17" /><span><strong>Mulai dari pemeriksaan sumber</strong><small>{{ reviewOpen?'Review resmi membuka Tindak Lanjut dan Keputusan.':'Menunggu review resmi dari penanggung jawab yang berwenang.' }}</small></span><button v-if="reviewOpen" class="link" @click="changeTab('review')"><AppIcon name="arrow" :size="14" />Catat review</button></div>

  <ProcessOutlet id="workspace-process-body" :view-key="tab" :label="tabs.find(item=>item[0]===tab)?.[1]">
  <template v-if="tab==='summary'">
   <div class="ws-reference-detail-grid" :class="{'ws-detail-no-card':!detail.official_card}"><section v-if="detail.official_card" class="card ws-official-card" :data-category="detail.report.event_type"><header class="section-heading"><div><div class="eyebrow">VERSI RESMI TERSIMPAN</div><h2>Incident Card resmi</h2></div><WorkspaceStatus :value="detail.report.validation_status" /></header><div class="ws-incident-title"><span class="heading-icon"><AppIcon :name="detail.report.event_type==='FLOOD'?'waves':detail.report.event_type==='FIRE'?'flame':detail.report.event_type==='ACCIDENT'?'car':'pulse'" :size="28" /></span><strong>{{ label(detail.report.event_type) }}</strong><span v-if="detail.ai?.sena" class="muted">SENA {{ label(detail.ai.sena.category) }}: {{ (detail.ai.sena.confidence*100).toFixed(2) }}%</span></div><p v-if="detail.official_card.uncertain" class="notice warning">Kartu memuat ketidakpastian. Pemeriksaan petugas tetap memerlukan pembandingan dengan bukti resmi.</p><dl class="incident-fields"><div v-for="(name,key) in fieldLabels" :key="key" class="incident-field"><dt>{{ name }}</dt><dd>{{ show(detail.official_card.data?.[key]) }}</dd></div></dl><p class="fine">Isi Reporter dan hasil mentah AI ditampilkan sebagai sumber baca. Review petugas disimpan terpisah.</p></section><aside><section class="card"><h2>Status penanganan</h2><dl class="ws-definition"><dt>Review</dt><dd><WorkspaceStatus :value="detail.report.validation_status" /></dd><dt>Tindak lanjut</dt><dd>{{ detail.followups.filter(x=>x.status==='PENDING').length }} menunggu, {{ detail.followups.filter(x=>x.status!=='PENDING').length }} selesai/dibatalkan</dd><dt>Arah keputusan</dt><dd>{{ detail.report.publication_status==='PENDING_APPROVAL'?'Siapkan publikasi':workspaceLabel(detail.report.publication_status) }}</dd><dt>Status publikasi</dt><dd><WorkspaceStatus :value="detail.report.publication_status" /></dd><dt>Kandidat aktif</dt><dd>{{ detail.has_active_candidate?'Ada':'Tidak ada' }}</dd><dt>Penutupan</dt><dd>{{ closed?'Ditutup':'Terbuka' }}</dd></dl></section><section class="card"><h2>Metadata laporan resmi</h2><dl class="ws-definition"><dt>ID laporan</dt><dd>{{ detail.report.id }}</dd><dt>Versi resmi</dt><dd>{{ detail.report.official_version }}</dd><dt>Kategori</dt><dd>{{ label(detail.report.event_type) }}</dd><dt>Waktu pengiriman</dt><dd>{{ date(detail.report.submitted_at) }}</dd><dt>Penanggung jawab</dt><dd>{{ detail.assignment?.operator_name||'Belum ditugaskan' }}</dd><dt>Revisi data</dt><dd>{{ detail.report.revision }}</dd></dl></section></aside></div>
   <section class="card"><h2>Riwayat penugasan</h2><div class="ws-table-scroll"><table class="ws-table"><thead><tr><th>Petugas</th><th>Mulai</th><th>Berakhir</th><th>Oleh</th><th>Alasan</th></tr></thead><tbody><tr v-for="item in detail.assignments" :key="item.id"><td>{{ item.operator_name }}<small>{{ workspaceLabel(item.source) }}</small></td><td>{{ date(item.started_at) }}</td><td>{{ item.ended_at?date(item.ended_at):'Penanggung jawab saat ini' }}</td><td>{{ item.assigned_by_name }}</td><td>{{ item.reason||'Klaim mandiri' }}</td></tr></tbody></table></div><p v-if="!detail.assignments.length" class="muted">Laporan belum memiliki penanggung jawab.</p></section>
  </template>

  <section v-else-if="tab==='evidence'&&privateAccess" class="ws-evidence-tab" aria-label="Bukti versi resmi"><WorkspaceEvidence :bundle="detail.official_bundle" :allowed="privateAccess" /></section>
  <template v-else-if="tab==='ai'&&privateAccess"><WorkspaceAi :detail="detail" /></template>

  <template v-else-if="tab==='review'">
<div class="ws-review-layout"><section v-if="reviewOpen" class="card ws-review-form"><header class="ws-tone-heading"><h2>Catat review resmi</h2><p>Pemeriksaan untuk laporan {{ shortId(detail.report.id) }} · versi resmi {{ detail.report.official_version }}.</p></header><div class="ws-tone-body"><form @submit.prevent="saveReview"><div class="field"><label for="review-outcome">Hasil review *</label><select id="review-outcome" v-model="review.outcome" :disabled="saving" required><option disabled value="">Pilih hasil review</option><option value="VALID">Valid</option><option value="INVALID">Tidak valid</option><option value="INCONCLUSIVE">Belum dapat disimpulkan</option></select></div><div class="field"><label for="review-reason">Alasan review *</label><textarea id="review-reason" v-model="review.reason" required maxlength="3000" placeholder="Jelaskan hasil pemeriksaan bukti dan alasan penilaian Anda." :disabled="saving" /></div><p class="fine">Hasil dan alasan wajib diisi sebelum disimpan.</p><button class="primary" :disabled="mutationBlocked||!review.outcome||!review.reason.trim()">{{ saving?'Menyimpan…':'Simpan review' }}</button></form></div></section><section v-else class="card"><h2>Review resmi tersimpan</h2><p v-if="detail.reviews.length"><WorkspaceStatus :value="detail.report.validation_status" /></p><p v-else class="muted">Review mengikuti penanggung jawab yang berwenang.</p><button v-if="!reportTabLocked(detail,'followup')" @click="changeTab('followup')">Lanjutkan penanganan</button></section><aside class="card ws-review-reference"><header class="ws-tone-heading"><h2>Acuan pemeriksaan</h2><p>Versi resmi {{ detail.report.official_version }}</p></header><div class="ws-tone-body"><p>Baca bukti dan narasi sebelum menentukan hasil review.</p><div v-if="privateAccess" class="ws-reference-actions"><button @click="changeTab('evidence')"><AppIcon name="arrow" :size="14" />Periksa bukti</button><button @click="changeTab('ai')"><AppIcon name="arrow" :size="14" />Baca narasi & hasil AI</button></div><p class="fine">Review petugas disimpan terpisah dari sumber Reporter dan hasil model.</p></div></aside></div>
   <section class="card"><h2>Riwayat review</h2><p v-if="!detail.reviews.length" class="muted">Belum ada review resmi.</p><ol class="ws-timeline"><li v-for="item in detail.reviews" :key="item.id"><WorkspaceStatus :value="item.outcome" /><p v-if="item.reason" class="preserve">{{ item.reason }}</p><small>{{ item.operator_name }} · {{ date(item.reviewed_at) }} · Versi resmi {{ detail.report.official_version }}</small></li></ol></section>
  </template>

  <template v-else-if="tab==='followup'">
   <section v-if="reviewReceipt" class="card ws-review-receipt" role="status"><AppIcon name="circle-check" :size="30" /><div><h2 data-process-heading>Review Anda sudah tersimpan</h2><p><WorkspaceStatus :value="reviewReceipt.outcome" /> · Versi resmi {{ detail.report.official_version }} · {{ date(reviewReceipt.reviewed_at) }}</p><small>Catat tindak lanjut bila diperlukan, lalu lanjutkan ke Keputusan.</small></div></section>
   <section v-if="handlerCan(session.user,detail,'manage_followup')" class="card ws-followup-form"><header class="ws-tone-heading"><h2>Tambahkan tindak lanjut</h2><p>Tindak lanjut baru berstatus Menunggu.</p></header><div class="ws-tone-body"><p v-if="!detail.reviews.length" class="notice warning">Catat review resmi terlebih dahulu.</p><form @submit.prevent="saveFollowup"><div class="field"><label for="followup-description">Catatan tindak lanjut *</label><textarea id="followup-description" v-model="followup" required maxlength="3000" :disabled="saving||!detail.reviews.length" /></div><button class="primary" :disabled="mutationBlocked||!detail.reviews.length||!followup.trim()">{{ saving?'Menyimpan…':'Tambah tindak lanjut' }}</button></form></div></section>
   <section class="card"><h2>Daftar tindak lanjut</h2><p v-if="!detail.followups.length" class="muted">Belum ada tindak lanjut yang dicatat.</p><ol class="ws-timeline"><li v-for="item in detail.followups" :key="item.id"><WorkspaceStatus :value="item.status" /><p v-if="item.description" class="preserve">{{ item.description }}</p><small>Dibuat oleh {{ item.operator_name }} · {{ date(item.created_at) }}</small><p v-if="item.completion_reason">{{ item.completion_reason }}</p><small v-if="item.finished_at">Selesai/dibatalkan pada {{ date(item.finished_at) }}</small><div v-if="item.status==='PENDING'&&handlerCan(session.user,detail,'manage_followup')" class="actions"><button :disabled="saving" @click="finishing(item,'DONE')">Selesaikan</button><button :disabled="saving" @click="finishing(item,'CANCELLED')">Batalkan tindak lanjut</button></div></li></ol></section>
   <div class="ws-process-navigation"><button :disabled="mutationBlocked" @click="changeTab('review')"><AppIcon name="left" :size="15" />Kembali ke review</button><button class="primary" :disabled="mutationBlocked" @click="changeTab('decision')">Lanjut ke keputusan<AppIcon name="arrow" :size="15" /></button></div>
  </template>

  <template v-else-if="tab==='decision'">
<div class="ws-decision-layout"><div class="ws-decision-main"><section class="card ws-direction-form"><header class="ws-tone-heading"><h2>Arah keputusan</h2></header><div class="ws-tone-body"><p><WorkspaceStatus :value="detail.report.publication_status" /></p><p v-if="detail.decision_reason" class="preserve">{{ detail.decision_reason }}</p><p v-if="detail.report.publication_status==='PENDING_APPROVAL'" class="notice">Isi publikasi belum terbit. Periksa pratinjau, konfirmasi isinya, lalu publikasikan di bawah.</p><form v-if="handlerCan(session.user,detail,'publish_report')&&!detail.has_active_candidate&&(!detail.report.published_version_id||decision.decision==='PREPARE')" @submit.prevent="saveDecision"><div class="field"><label for="publication-direction">Keputusan *</label><select id="publication-direction" v-model="decision.decision" :disabled="mutationBlocked||detail.has_active_candidate"><option disabled value="">Pilih keputusan</option><option value="INTERNAL" :disabled="Boolean(detail.report.published_version_id)">Tetap internal</option><option value="PREPARE" :disabled="detail.report.validation_status!=='VALID'">Tinjau untuk publikasi</option></select><small>Pilih publikasi untuk langsung memeriksa isi dan pratinjau. Review Tidak valid atau Belum dapat disimpulkan tetap internal.</small></div><div class="field"><label for="publication-reason">Alasan keputusan *</label><textarea id="publication-reason" v-model="decision.reason" required maxlength="3000" :disabled="mutationBlocked" /></div><button v-if="decision.decision==='INTERNAL'" class="primary" :disabled="mutationBlocked||!decision.reason.trim()||!decisionAllowed(detail,decision.decision)">{{ saving?'Menyimpan…':'Simpan keputusan' }}</button></form><button v-if="handlerCan(session.user,detail,'publish_report')&&detail.report.published_version_id&&!detail.has_active_candidate&&decision.decision!=='PREPARE'" @click="decision.decision='PREPARE'">Tinjau pembaruan informasi</button></div></section>
</div><section class="card ws-closure-panel"><header class="ws-tone-heading"><h2>Penutupan laporan</h2><p>Seluruh syarat berikut perlu terpenuhi.</p></header><div class="ws-tone-body"><ul class="ws-requirements"><li v-for="item in detail.close_requirements" :key="item.key"><AppIcon :name="item.met?'circle-check':'clock'" :size="19" :class="{'text-success':item.met}" /><span>{{ item.label }}</span><strong>{{ item.met?'Terpenuhi':'Belum terpenuhi' }}</strong></li></ul><p class="fine">Review yang sah dapat berupa VALID, INVALID, atau INCONCLUSIVE. Penutupan tidak mensyaratkan hasil selalu VALID.</p><button v-if="handlerCan(session.user,detail,'close_report')" class="danger" :disabled="mutationBlocked||!closeAllowed(session.user,detail)" @click="closing=true">Tutup laporan</button><p v-if="detail.closure_note" class="preserve">Catatan penutupan: {{ detail.closure_note }}</p></div></section>
   <PublicationPanel class="ws-publication-section" :key="detail.report.id" :detail="detail" :blocked="saving||busy||uncertain" :start="decision.decision==='PREPARE'" :decision-reason="decision.reason" @busy="publicationSaving=$event" @saved="publicationSaved" />
</div>
  </template>

  <section v-else-if="tab==='history'" class="card"><div class="section-heading"><div><h2>Riwayat laporan</h2><p class="muted">Aktivitas terbaru ditampilkan di bagian atas.</p></div><button :aria-pressed="technical" @click="technical=!technical">{{ technical?'Sembunyikan peristiwa teknis':'Tampilkan peristiwa teknis' }}</button></div><p v-if="!historyRows.length" class="muted">Belum ada riwayat yang dapat ditampilkan.</p><ol class="ws-timeline"><li v-for="item in historyRows" :key="item.id"><strong>{{ eventLabels[item.action]||'Pembaruan laporan' }}</strong><small>{{ item.actor_name }} / {{ roleLabel(item.actor_role) }} · {{ date(item.created_at) }}</small><details><summary>Referensi aktivitas</summary><code>{{ item.action }}</code></details><div class="ws-state-row"><WorkspaceStatus v-for="(value,key) in item.states" :key="key" :value="key==='revision'?'Revisi '+value:value" /></div></li></ol></section>

  </ProcessOutlet>

  <WorkspaceAssignment v-if="assignment" :report="{...detail.report,operator_id:detail.assignment?.operator_id||null,operator_name:detail.assignment?.operator_name||null}" @close="assignment=false" @saved="assigned" />
  <AppDialog v-if="closing" title="Tutup laporan?" :caption="shortId(detail.report.id)" @close="!saving&&(closing=false)"><ErrorNotice :error="error" /><p>Penutupan mengunci perubahan laporan dan mempertahankan sumber serta riwayatnya.</p><form id="closure-form" @submit.prevent="close"><div class="field"><label for="closure-note">Catatan penutupan *</label><textarea id="closure-note" v-model="closure" required maxlength="3000" :disabled="saving" /></div></form><template #actions><button :disabled="saving" @click="closing=false">Batal</button><button class="danger" type="submit" form="closure-form" :disabled="mutationBlocked||!closure.trim()">{{ saving?'Menutup…':'Tutup laporan' }}</button></template></AppDialog>
  <AppDialog v-if="finish" :title="finish.nextStatus==='DONE'?'Selesaikan tindak lanjut':'Batalkan tindak lanjut'" @close="!saving&&(finish=null)"><ErrorNotice :error="error" /><p class="preserve">{{ finish.description }}</p><form id="finish-form" @submit.prevent="saveFinish"><div class="field"><label for="finish-reason">Catatan / alasan *</label><textarea id="finish-reason" v-model="finishReason" required maxlength="3000" :disabled="saving" /></div></form><template #actions><button :disabled="saving" @click="finish=null">Kembali</button><button class="primary" type="submit" form="finish-form" :disabled="mutationBlocked||!finishReason.trim()">{{ saving?'Menyimpan…':'Simpan tindak lanjut' }}</button></template></AppDialog>
 </template>
</template>
