<script setup>
import {computed,onBeforeUnmount,onMounted,reactive,ref,watch} from 'vue';
import {useRoute} from 'vue-router';
import {api} from '../api';
import {session} from '../session';
import {date,label} from '../domain';
import {fieldLabels} from '../analysis';
import {hasPermission,handlerCan,closeAllowed,decisionAllowed,shortId,workspaceLabel,eventLabels,roleLabel,reportTabLocked} from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
import WorkspaceStatus from '../components/WorkspaceStatus.vue';
import WorkspaceAssignment from '../components/WorkspaceAssignment.vue';
import WorkspaceEvidence from '../components/WorkspaceEvidence.vue';
const route=useRoute();
const detail=ref(null),busy=ref(false),saving=ref(false),error=ref(null),message=ref(''),tab=ref('summary');
const assignment=ref(false),closing=ref(false),finish=ref(null);
const uncertain=ref(false);
const mutationBlocked=computed(()=>saving.value||busy.value||uncertain.value);
const review=reactive({outcome:'VALID',reason:''}),followup=ref(''),decision=reactive({decision:'INTERNAL',reason:''}),closure=ref(''),finishReason=ref('');
const closed=computed(()=>detail.value?.report?.workflow_status==='CLOSED');
const privateAccess=computed(()=>detail.value?.private_access===true);
const tabs=computed(()=>[
 ['summary',privateAccess.value?'Ringkasan Resmi':'Ringkasan Monitoring'],
 ...(privateAccess.value?[['evidence','Bukti'],['ai','Narasi dan Hasil AI']]:[]),
 ['review','Review'],['followup','Tindak Lanjut'],['decision','Keputusan'],['history','Riwayat']
]);
const canAssign=computed(()=>session.user?.role==='ADMIN'&&hasPermission(session.user,'assign_report')&&!closed.value&&!uncertain.value);
const reviewOpen=computed(()=>handlerCan(session.user,detail.value,'review_report')&&!detail.value.has_active_candidate&&!['APPROVED','PUBLISHED'].includes(detail.value.report.publication_status));
const back=computed(()=>session.user?.role==='ADMIN'&&hasPermission(session.user,'monitor_report')?'/workspace/monitoring':'/workspace/assigned');
function show(value){if(value===null||value===undefined||value==='')return 'Belum tersedia';if(Array.isArray(value))return value.length?value.map(v=>typeof v==='object'?JSON.stringify(v):v).join('; '):'Belum tersedia';return typeof value==='object'?JSON.stringify(value):String(value);}
let generation=0,poll=null;
async function load({quiet=false}={}){
 const version=++generation,id=route.params.id;
 if(!quiet){busy.value=true;error.value=null;}
 try{const r=await api(`workspace/reports/${id}/`);if(version!==generation)return;detail.value=r.data;if(!tabs.value.some(x=>x[0]===tab.value))tab.value='summary';else if(reportTabLocked(detail.value,tab.value))tab.value='review';}
 catch(e){if(version===generation){detail.value=null;error.value=e;assignment.value=false;closing.value=false;finish.value=null;}}
 finally{if(version===generation)busy.value=false;}
}
async function write(action,body){
 if(saving.value||uncertain.value||!detail.value)return false;saving.value=true;error.value=null;message.value='';
 const revision=detail.value.report.revision;
 try{const r=await api(`workspace/reports/${detail.value.report.id}/${action}/`,{method:'POST',key:crypto.randomUUID(),body:{...body,expected_revision:revision}});message.value=r.data.message;await load();return true;}
 catch(e){
  // Always reconcile unknown responses or stale revisions before another action.
  await load({quiet:true});error.value=e;if(e.code==='RESPONSE_UNKNOWN'){uncertain.value=true;closing.value=false;finish.value=null;tab.value='history';}return false;
 }finally{saving.value=false;}
}
async function saveReview(){if(await write('reviews',{outcome:review.outcome,reason:review.reason.trim()}))review.reason='';}
async function saveFollowup(){if(!reportTabLocked(detail.value,'followup')&&await write('followups',{description:followup.value.trim()}))followup.value='';}
async function saveDecision(){if(!reportTabLocked(detail.value,'decision')&&await write('decision',{decision:decision.decision,reason:decision.reason.trim()}))decision.reason='';}
async function close(){if(await write('close',{closure_note:closure.value.trim()})){closing.value=false;closure.value='';}}
function finishing(item,status){finish.value={...item,nextStatus:status};finishReason.value='';}
async function saveFinish(){if(await write(`followups/${finish.value.id}`,{status:finish.value.nextStatus,completion_reason:finishReason.value.trim()}))finish.value=null;}
async function assigned(text){assignment.value=false;message.value=text;await load();}
function recheck(){if(!document.hidden&&navigator.onLine&&!saving.value&&!busy.value)load({quiet:true});}
watch(()=>route.params.id,()=>{detail.value=null;tab.value='summary';message.value='';uncertain.value=false;review.reason='';followup.value='';decision.reason='';load();},{immediate:true});
onMounted(()=>{window.addEventListener('focus',recheck);poll=setInterval(recheck,20000);});
onBeforeUnmount(()=>{generation+=1;clearInterval(poll);window.removeEventListener('focus',recheck);detail.value=null;});
</script>
<template>
 <div class="page-heading ws-page-heading"><div><div class="eyebrow">LAPORAN RESMI</div><h1>{{ privateAccess?'Detail Laporan':'Ringkasan Laporan' }}</h1><p class="subtitle">{{ shortId(route.params.id) }}<template v-if="detail"> · Versi resmi {{ detail.report.official_version }} · {{ label(detail.report.event_type) }}</template></p></div><RouterLink class="button" :to="back"><AppIcon name="left" :size="15" />Kembali</RouterLink></div>
 <ErrorNotice :error="error" /><p v-if="busy" class="ws-loading" role="status">Membaca keadaan terbaru laporan…</p><p v-if="message" class="notice success" role="status">{{ message }}</p>
 <div v-if="uncertain" class="notice warning" role="status">Respons tindakan terputus. Keadaan laporan telah dibaca ulang. Periksa riwayat sebelum melakukan tindakan berikutnya.<button @click="uncertain=false;error=null">Saya sudah memeriksa riwayat</button></div>
 <template v-if="detail">
  <div class="ws-report-toolbar"><div class="ws-state-row"><WorkspaceStatus :value="detail.report.workflow_status" /><WorkspaceStatus :value="detail.report.validation_status" /><WorkspaceStatus :value="detail.report.publication_status" /></div><button :disabled="busy||saving" @click="load()"><AppIcon name="refresh" :size="15" />Muat ulang</button><button v-if="canAssign" :disabled="busy||saving" @click="assignment=true">{{ detail.assignment?'Alihkan petugas':'Tugaskan laporan' }}</button></div>
  <p v-if="closed" class="notice success"><AppIcon name="lock" :size="17" />Laporan ditutup pada {{ date(detail.report.closed_at) }}. Perubahan laporan dan penugasan telah dikunci; pembacaan tetap mengikuti hak akses.</p>
  <p v-else-if="!privateAccess" class="ws-info-line"><AppIcon name="shield" :size="18" />Ringkasan administratif. Bukti, narasi, dan hasil AI privat hanya dapat dibaca penanggung jawab saat ini yang memiliki izin.</p>
  <nav class="ws-tabs" aria-label="Bagian laporan"><button v-for="[key,title] in tabs" :key="key" :class="{active:tab===key}" :disabled="reportTabLocked(detail,key)" :aria-describedby="reportTabLocked(detail,key)?'review-step-hint':undefined" :title="reportTabLocked(detail,key)?'Catat dan simpan review resmi terlebih dahulu.':undefined" :aria-current="tab===key?'page':undefined" @click="!reportTabLocked(detail,key)&&(tab=key)"><AppIcon v-if="reportTabLocked(detail,key)" name="lock" :size="14" />{{ title }}</button></nav>
  <p v-if="reportTabLocked(detail,'followup')" id="review-step-hint" class="ws-stage-hint"><AppIcon name="lock" :size="18" /><span><strong>Review resmi belum dicatat.</strong> {{ reviewOpen?'Buka tab Review dan simpan hasil beserta alasannya.':'Menunggu hasil review resmi dari penanggung jawab yang berwenang.' }} Tindak Lanjut dan Keputusan akan terbuka setelah review resmi tersimpan.</span></p>

  <template v-if="tab==='summary'">
   <div class="ws-detail-columns"><section class="card"><h2>Metadata laporan resmi</h2><dl class="ws-definition"><dt>ID laporan</dt><dd>{{ detail.report.id }}</dd><dt>Versi resmi</dt><dd>{{ detail.report.official_version }}</dd><dt>Kategori</dt><dd>{{ label(detail.report.event_type) }}</dd><dt>Waktu pengiriman</dt><dd>{{ date(detail.report.submitted_at) }}</dd><dt>Penanggung jawab</dt><dd>{{ detail.assignment?.operator_name||'Belum ditugaskan' }}</dd><dt>Revisi data</dt><dd>{{ detail.report.revision }}</dd></dl></section><section class="card"><h2>Status penanganan</h2><dl class="ws-definition"><dt>Review</dt><dd><WorkspaceStatus :value="detail.report.validation_status" /></dd><dt>Tindak lanjut</dt><dd>{{ detail.followups.filter(x=>x.status==='PENDING').length }} menunggu, {{ detail.followups.filter(x=>x.status!=='PENDING').length }} selesai/dibatalkan</dd><dt>Arah keputusan</dt><dd>{{ detail.report.publication_status==='PENDING_APPROVAL'?'Siapkan publikasi':workspaceLabel(detail.report.publication_status) }}</dd><dt>Status publikasi</dt><dd><WorkspaceStatus :value="detail.report.publication_status" /></dd><dt>Kandidat aktif</dt><dd>{{ detail.has_active_candidate?'Ada':'Tidak ada' }}</dd><dt>Penutupan</dt><dd>{{ closed?'Ditutup':'Terbuka' }}</dd></dl></section></div>
   <section v-if="detail.official_card" class="card ws-official-card"><header class="section-heading"><div><div class="eyebrow">VERSI RESMI TERSIMPAN</div><h2>Incident Card resmi</h2></div><WorkspaceStatus :value="detail.report.validation_status" /></header><div class="ws-incident-title"><span class="heading-icon"><AppIcon :name="detail.report.event_type==='FLOOD'?'waves':detail.report.event_type==='FIRE'?'flame':detail.report.event_type==='ACCIDENT'?'car':'pulse'" :size="28" /></span><strong>{{ label(detail.report.event_type) }}</strong><span v-if="detail.ai?.sena" class="muted">SENA {{ label(detail.ai.sena.category) }}: {{ (detail.ai.sena.confidence*100).toFixed(2) }}%</span></div><p v-if="detail.official_card.uncertain" class="notice warning">Kartu memuat ketidakpastian. Pemeriksaan petugas tetap memerlukan pembandingan dengan bukti resmi.</p><dl class="incident-fields"><div v-for="(name,key) in fieldLabels" :key="key" class="incident-field"><dt>{{ name }}</dt><dd>{{ show(detail.official_card.data?.[key]) }}</dd></div></dl><p class="fine">Isi Reporter dan hasil mentah AI ditampilkan sebagai sumber baca. Review petugas disimpan terpisah.</p></section>
   <section class="card"><h2>Riwayat penugasan</h2><div class="ws-table-scroll"><table class="ws-table"><thead><tr><th>Petugas</th><th>Mulai</th><th>Berakhir</th><th>Oleh</th><th>Alasan</th></tr></thead><tbody><tr v-for="item in detail.assignments" :key="item.id"><td>{{ item.operator_name }}<small>{{ workspaceLabel(item.source) }}</small></td><td>{{ date(item.started_at) }}</td><td>{{ item.ended_at?date(item.ended_at):'Penanggung jawab saat ini' }}</td><td>{{ item.assigned_by_name }}</td><td>{{ item.reason||'Klaim mandiri' }}</td></tr></tbody></table></div><p v-if="!detail.assignments.length" class="muted">Laporan belum memiliki penanggung jawab.</p></section>
  </template>

  <section v-else-if="tab==='evidence'&&privateAccess" class="card"><h2>Bukti versi resmi</h2><WorkspaceEvidence :bundle="detail.official_bundle" :allowed="privateAccess" /></section>

  <template v-else-if="tab==='ai'&&privateAccess"><section class="card"><div class="eyebrow">SUMBER PEMERIKSAAN</div><h2>Narasi resmi</h2><p class="preserve ws-source-text">{{ detail.official_narrative?.text||'Narasi belum tersedia.' }}</p><p class="fine">Narasi adalah sumber versi resmi yang dikirim Reporter.</p></section><section class="card"><h2>Hasil AI mentah</h2><p class="muted">Hasil model menjadi bahan pemeriksaan, terpisah dari keputusan review manusia.</p><h3>SENA</h3><p>{{ label(detail.ai?.sena?.category) }} · {{ detail.ai?.sena?.model_version }}</p><details><summary>Baca keluaran mentah SENA</summary><pre class="ws-json">{{ JSON.stringify(detail.ai?.sena?.raw_output,null,2) }}</pre></details><h3>NARA</h3><p>{{ detail.ai?.nara?.model_version }}</p><dl class="ws-definition"><template v-for="(value,key) in detail.ai?.nara?.normalized_output||{}" :key="key"><dt>{{ fieldLabels[key]||key }}</dt><dd>{{ show(value) }}</dd></template></dl><details><summary>Baca keluaran mentah NARA</summary><pre class="ws-json">{{ JSON.stringify(detail.ai?.nara?.raw_output,null,2) }}</pre></details></section></template>

  <template v-else-if="tab==='review'">
   <section v-if="reviewOpen" class="card"><h2>Catat review resmi</h2><p class="muted">Review mengacu pada versi resmi {{ detail.report.official_version }}. Isi Reporter dan keluaran mentah AI tetap dipertahankan.</p><form @submit.prevent="saveReview"><div class="field"><label for="review-outcome">Hasil review *</label><select id="review-outcome" v-model="review.outcome" :disabled="saving" required><option value="VALID">VALID — Valid</option><option value="INVALID">INVALID — Tidak valid</option><option value="INCONCLUSIVE">INCONCLUSIVE — Belum dapat dipastikan</option></select></div><div class="field"><label for="review-reason">Alasan review *</label><textarea id="review-reason" v-model="review.reason" required maxlength="3000" :disabled="saving" /></div><button class="primary" :disabled="mutationBlocked||!review.reason.trim()">{{ saving?'Menyimpan…':'Simpan review' }}</button></form></section>
   <section class="card"><h2>Riwayat review</h2><p v-if="!detail.reviews.length" class="muted">Belum ada review resmi.</p><ol class="ws-timeline"><li v-for="item in detail.reviews" :key="item.id"><WorkspaceStatus :value="item.outcome" /><p v-if="item.reason" class="preserve">{{ item.reason }}</p><small>{{ item.operator_name }} · {{ date(item.reviewed_at) }} · Versi resmi {{ detail.report.official_version }}</small></li></ol></section>
  </template>

  <template v-else-if="tab==='followup'">
   <section v-if="handlerCan(session.user,detail,'manage_followup')" class="card"><h2>Tambahkan tindak lanjut</h2><p v-if="!detail.reviews.length" class="notice warning">Catat review resmi terlebih dahulu.</p><form @submit.prevent="saveFollowup"><div class="field"><label for="followup-description">Catatan tindak lanjut *</label><textarea id="followup-description" v-model="followup" required maxlength="3000" :disabled="saving||!detail.reviews.length" /></div><button class="primary" :disabled="mutationBlocked||!detail.reviews.length||!followup.trim()">{{ saving?'Menyimpan…':'Tambah tindak lanjut' }}</button></form></section>
   <section class="card"><h2>Daftar tindak lanjut</h2><p v-if="!detail.followups.length" class="muted">Belum ada tindak lanjut yang dicatat.</p><ol class="ws-timeline"><li v-for="item in detail.followups" :key="item.id"><WorkspaceStatus :value="item.status" /><p v-if="item.description" class="preserve">{{ item.description }}</p><small>Dibuat oleh {{ item.operator_name }} · {{ date(item.created_at) }}</small><p v-if="item.completion_reason">{{ item.completion_reason }}</p><small v-if="item.finished_at">Selesai/dibatalkan pada {{ date(item.finished_at) }}</small><div v-if="item.status==='PENDING'&&handlerCan(session.user,detail,'manage_followup')" class="actions"><button :disabled="saving" @click="finishing(item,'DONE')">Selesaikan</button><button :disabled="saving" @click="finishing(item,'CANCELLED')">Batalkan tindak lanjut</button></div></li></ol></section>
  </template>

  <template v-else-if="tab==='decision'">
   <section class="card"><h2>Arah keputusan</h2><p><WorkspaceStatus :value="detail.report.publication_status" /></p><p v-if="detail.decision_reason" class="preserve">{{ detail.decision_reason }}</p><p v-if="detail.report.publication_status==='PENDING_APPROVAL'" class="notice">Laporan belum dipublikasikan. Penerbitan memerlukan kandidat publikasi dan persetujuan pada alur publikasi.</p><form v-if="handlerCan(session.user,detail,'publish_report')" @submit.prevent="saveDecision"><div class="field"><label for="publication-direction">Keputusan *</label><select id="publication-direction" v-model="decision.decision" :disabled="saving"><option value="INTERNAL">Tetap internal</option><option value="PREPARE" :disabled="detail.report.validation_status!=='VALID'">Siapkan publikasi</option></select><small>INVALID dan INCONCLUSIVE tetap internal. Persiapan publikasi belum menerbitkan laporan.</small></div><div class="field"><label for="publication-reason">Alasan keputusan *</label><textarea id="publication-reason" v-model="decision.reason" required maxlength="3000" :disabled="saving" /></div><button class="primary" :disabled="mutationBlocked||!decision.reason.trim()||!decisionAllowed(detail,decision.decision)">{{ saving?'Menyimpan…':'Simpan keputusan' }}</button></form></section>
   <section class="card"><h2>Penutupan laporan</h2><ul class="ws-requirements"><li v-for="item in detail.close_requirements" :key="item.key"><AppIcon :name="item.met?'circle-check':'clock'" :size="19" :class="{'text-success':item.met}" /><span>{{ item.label }}</span><strong>{{ item.met?'Terpenuhi':'Belum terpenuhi' }}</strong></li></ul><p class="fine">Review yang sah dapat berupa VALID, INVALID, atau INCONCLUSIVE. Penutupan tidak mensyaratkan hasil selalu VALID.</p><button v-if="handlerCan(session.user,detail,'close_report')" class="danger" :disabled="mutationBlocked||!closeAllowed(session.user,detail)" @click="closing=true">Tutup laporan</button><p v-if="detail.closure_note" class="preserve">Catatan penutupan: {{ detail.closure_note }}</p></section>
  </template>

  <section v-else-if="tab==='history'" class="card"><h2>Riwayat laporan</h2><p v-if="!detail.history?.length" class="muted">Belum ada riwayat yang dapat ditampilkan.</p><ol class="ws-timeline"><li v-for="item in detail.history||[]" :key="item.id"><strong>{{ eventLabels[item.action]||item.action }}</strong><small>{{ item.actor_name }} / {{ roleLabel(item.actor_role) }} · {{ date(item.created_at) }}</small><div class="ws-state-row"><WorkspaceStatus v-for="(value,key) in item.states" :key="key" :value="key==='revision'?'Revisi '+value:value" /></div></li></ol></section>

  <WorkspaceAssignment v-if="assignment" :report="detail.report" @close="assignment=false" @saved="assigned" />
  <AppDialog v-if="closing" title="Tutup laporan?" :caption="shortId(detail.report.id)" @close="!saving&&(closing=false)"><ErrorNotice :error="error" /><p>Penutupan mengunci perubahan laporan dan mempertahankan sumber serta riwayatnya.</p><form id="closure-form" @submit.prevent="close"><div class="field"><label for="closure-note">Catatan penutupan *</label><textarea id="closure-note" v-model="closure" required maxlength="3000" :disabled="saving" /></div></form><template #actions><button :disabled="saving" @click="closing=false">Batal</button><button class="danger" type="submit" form="closure-form" :disabled="mutationBlocked||!closure.trim()">{{ saving?'Menutup…':'Tutup laporan' }}</button></template></AppDialog>
  <AppDialog v-if="finish" :title="finish.nextStatus==='DONE'?'Selesaikan tindak lanjut':'Batalkan tindak lanjut'" @close="!saving&&(finish=null)"><ErrorNotice :error="error" /><p class="preserve">{{ finish.description }}</p><form id="finish-form" @submit.prevent="saveFinish"><div class="field"><label for="finish-reason">Catatan / alasan *</label><textarea id="finish-reason" v-model="finishReason" required maxlength="3000" :disabled="saving" /></div></form><template #actions><button :disabled="saving" @click="finish=null">Kembali</button><button class="primary" type="submit" form="finish-form" :disabled="mutationBlocked||!finishReason.trim()">{{ saving?'Menyimpan…':'Simpan tindak lanjut' }}</button></template></AppDialog>
 </template>
</template>
