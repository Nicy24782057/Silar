<script setup>
import {computed,reactive,ref,watch,onBeforeUnmount} from 'vue';
import {useRoute,useRouter} from 'vue-router';
import {api,ApiError} from '../api';
import {online} from '../network';
import {requiresStoredState} from '../recovery';
import {session} from '../session';
import {date,label,paginationPath} from '../domain';
import {hasPermission,shortId,categoryOptions,workflowOptions,workspaceReportsPath,workspaceQuickView,workspaceEffectiveFilters,adminReportsScope,ADMIN_REPORTS_PATH,ADMIN_REPORTS_TITLE} from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
import FetchState from '../components/FetchState.vue';
import WorkspaceStatus from '../components/WorkspaceStatus.vue';
import WorkspaceAssignment from '../components/WorkspaceAssignment.vue';
const route=useRoute(),router=useRouter();
const adminPage=computed(()=>route.meta.workspaceScope==='admin');
const scope=computed(()=>adminPage.value?(adminReportsScope(session.user)||'monitor'):route.meta.workspaceScope||'assigned');
const quickView=computed(()=>workspaceQuickView(scope.value,route.query.view));
const listPath=computed(()=>({queue:'/workspace/queue',assigned:'/workspace/assigned',monitor:ADMIN_REPORTS_PATH,assignment:ADMIN_REPORTS_PATH}[scope.value]));
const clearLabel=computed(()=>scope.value==='assigned'?'Tampilkan semua penanganan':'Tampilkan semua laporan');
const titles={queue:'Antrean Laporan',assigned:'Penanganan Saya',monitor:ADMIN_REPORTS_TITLE,assignment:ADMIN_REPORTS_TITLE};
const captions={queue:'Ringkasan laporan resmi yang belum memiliki penanggung jawab.',assigned:'Laporan yang menjadi tanggung jawab akun Anda saat ini.',monitor:'Pantau status laporan resmi dan penanggung jawab sesuai kewenangan.',assignment:'Pantau status laporan resmi, tetapkan penanggung jawab, dan catat setiap pengalihan.'};
const filters=reactive({q:'',event_type:'',workflow_status:'',ordering:'-submitted_at'});
const rows=ref([]),count=ref(0),next=ref(null),previous=ref(null),busy=ref(false),error=ref(null),message=ref('');
const readError=ref(null);
const selected=ref(null),summary=ref(null),summaryBusy=ref(false),summaryError=ref(null);let summarySequence=0,summaryAbort;
function closeSummary(){++summarySequence;summaryAbort?.abort();selected.value=null;summary.value=null;summaryError.value=null;}
async function readSummary(){const row=selected.value;if(!row)return;const version=++summarySequence;summaryAbort?.abort();summaryAbort=new AbortController();summaryBusy.value=true;summaryError.value=null;summary.value=null;
 try{const result=(await api(`workspace/reports/${row.id}/`,{signal:summaryAbort.signal})).data;if(version!==summarySequence)return;if(result.report?.id!==row.id)throw new ApiError('Ringkasan tidak sesuai laporan yang dipilih.','INVALID_RESPONSE');summary.value=result;}
 catch(e){if(version===summarySequence&&e.name!=='AbortError')summaryError.value=e;}finally{if(version===summarySequence)summaryBusy.value=false;}}
function openSummary(row){selected.value=row;readSummary();}
watch(()=>route.query.laporan,id=>{if(adminPage.value&&typeof id==='string'&&id)openSummary({id});},{immediate:true});
onBeforeUnmount(()=>{generation++;closeSummary();});

const assignment=ref(null),claimReport=ref(null),claiming=ref(false),claimUnknown=ref(false),claimError=ref(null);let generation=0,claimKey=null;
const canAssign=computed(()=>session.user?.role==='ADMIN'&&hasPermission(session.user,'assign_report'));
const canClaim=computed(()=>hasPermission(session.user,'claim_report')&&hasPermission(session.user,'view_assigned_report'));
async function load(path){
  const version=++generation;busy.value=true;error.value=null;readError.value=null;
  try{const r=await api(path||workspaceReportsPath(scope.value,{...workspaceEffectiveFilters(filters,quickView.value),q:filters.q.trim().replace(/^#/, '')}));if(version!==generation)return;rows.value=r.results;count.value=r.count;next.value=r.next;previous.value=r.previous;}
  catch(e){if(version===generation){readError.value=e;rows.value=[];count.value=0;next.value=null;previous.value=null;}}
  finally{if(version===generation)busy.value=false;}
}
watch([scope,()=>route.query.view],()=>{Object.assign(filters,{q:'',event_type:'',workflow_status:quickView.value?.filters?.workflow_status||'',ordering:'-submitted_at'});message.value='';assignment.value=null;claimReport.value=null;load();},{immediate:true});
function openClaim(row){claimReport.value=row;claimKey=crypto.randomUUID();claimUnknown.value=false;claimError.value=null;error.value=null;}
async function claim(){
  if(claiming.value||!claimReport.value)return;claiming.value=true;error.value=null;
  try{const row=claimReport.value;await api(`workspace/reports/${row.id}/claim/`,{method:'POST',key:claimKey,body:{expected_revision:row.revision}});claimReport.value=null;await router.push('/workspace/reports/'+row.id);}
  catch(e){if(requiresStoredState(e)){claimUnknown.value=true;claimError.value=e;}else{claimReport.value=null;await load();error.value=e;}}finally{claiming.value=false;}
}
async function assigned(text){assignment.value=null;message.value=text;await load();}
</script>
<template>
 <div class="page-heading ws-page-heading"><div><div class="eyebrow">RUANG KERJA {{ session.user?.role==='ADMIN'?'ADMIN':'OPERATOR' }}</div><h1>{{ quickView?.title||titles[scope] }}</h1><p class="subtitle">{{ quickView?.caption||captions[scope] }}</p></div><button :disabled="busy" @click="load()"><AppIcon name="refresh" :size="15" />Muat ulang</button></div>
 <ErrorNotice :error="error" /><p v-if="message" class="notice success" role="status">{{ message }}</p>
 <p v-if="quickView" class="ws-quick-filter"><span><AppIcon name="search" :size="17" />Tampilan: {{ quickView.title }}</span><RouterLink :to="listPath">{{ clearLabel }}<AppIcon name="arrow" :size="15" /></RouterLink></p>
 <div class="shared-info-banner"><AppIcon name="shield" :size="22" /><div><strong>{{ scope==='queue'?'Antrean menampilkan ringkasan resmi.':adminPage?'Penugasan mengikuti kewenangan akun.':'Penanganan mengikuti penugasan dan kewenangan akun.' }}</strong><p>{{ scope==='queue'?'Identitas Reporter dan bukti privat tersedia setelah penugasan berhasil, sesuai izin akun.':'Akses administratif tidak otomatis memberikan hak membaca bukti atau melakukan tindakan Operator.' }}</p></div></div>
 <section class="card ws-table-panel" :aria-busy="busy">
  <header class="ws-panel-heading"><div><h2>{{ adminPage?'Daftar laporan dan penugasan':'Daftar laporan resmi' }}</h2><p>{{ busy?'Membaca jumlah laporan…':readError?'Jumlah belum tersedia':count+' laporan sesuai hak akses Anda.' }}</p></div></header>
  <form class="ws-filters" @submit.prevent="load()"><label class="ws-search"><AppIcon name="search" :size="17" /><span class="sr-only">Cari ID laporan</span><input v-model="filters.q" placeholder="Cari ID laporan" maxlength="37"></label><label><span class="sr-only">Kategori</span><select v-model="filters.event_type" @change="load()"><option value="">Semua kategori</option><option v-for="item in categoryOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select></label><label v-if="scope!=='queue'"><span class="sr-only">Tahap laporan</span><select v-model="filters.workflow_status" :disabled="Boolean(quickView?.filters?.workflow_status)" :title="quickView?.filters?.workflow_status?'Tahap mengikuti kartu dashboard. Pilih Tampilkan semua laporan untuk mengubah tahap.':undefined" @change="load()"><option value="">Semua tahap</option><option v-for="item in workflowOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select></label><label><span class="sr-only">Urutan</span><select v-model="filters.ordering" @change="load()"><option value="-submitted_at">Terbaru</option><option value="submitted_at">Terlama</option></select></label><button type="submit" :disabled="busy">Cari</button></form>
  <FetchState v-if="busy" compact title="Memuat laporan…" description="Membaca laporan resmi sesuai kewenangan akun." /><FetchState v-else-if="readError" state="error" compact title="Daftar laporan belum dapat dimuat" description="Coba lagi untuk membaca laporan tersimpan." :error="readError" :disabled="busy" @retry="load()" />
  <FetchState v-else-if="!rows.length" state="empty" compact :title="scope==='queue'?'Belum ada laporan dalam antrean':'Belum ada laporan yang sesuai'" :description="scope==='assigned'?'Laporan akan muncul setelah Anda mengklaim atau menerima penugasan dari Admin.':'Ubah filter atau muat ulang untuk memeriksa keadaan terbaru.'" />
  <div v-if="!busy&&!readError&&rows.length" class="ws-table-scroll"><table class="ws-table"><thead><tr><th>Laporan</th><th>Kategori</th><th>Status</th><th v-if="scope!=='queue'">Penanggung jawab</th><th>Aksi</th></tr></thead><tbody><tr v-for="row in rows" :key="row.id"><td><strong :title="row.id">{{ shortId(row.id) }}</strong><small>{{ date(row.submitted_at) }}</small><small>Versi resmi {{ row.official_version }}</small></td><td>{{ label(row.event_type) }}</td><td><WorkspaceStatus :value="row.workflow_status" /></td><td v-if="scope!=='queue'">{{ row.operator_name||'Belum ditugaskan' }}</td><td class="ws-row-actions"><template v-if="scope==='queue'"><button class="primary small" :disabled="busy||!canClaim" @click="openClaim(row)">Klaim laporan</button><small v-if="!canClaim">Izin klaim belum diberikan</small></template><template v-else><button v-if="adminPage" class="link" @click="openSummary(row)">Ringkasan</button><RouterLink v-else class="ws-text-link" :to="'/workspace/reports/'+row.id">Lihat {{ scope==='assigned'?'detail':'ringkasan' }}<AppIcon name="arrow" :size="13" /></RouterLink><button v-if="canAssign&&scope==='assignment'" class="link" :disabled="busy||row.workflow_status==='CLOSED'" @click="assignment=row">{{ row.operator_id?'Alihkan':'Tugaskan' }}</button></template></td></tr></tbody></table></div>
  <footer v-if="!busy&&!readError" class="ws-pagination"><span>{{ count }} laporan</span><div><button :disabled="busy||!previous" @click="load(paginationPath(previous))">Sebelumnya</button><button :disabled="busy||!next" @click="load(paginationPath(next))">Berikutnya</button></div></footer>
 </section>
 <WorkspaceAssignment v-if="assignment" :report="assignment" @close="assignment=null" @saved="assigned" />
 <AppDialog v-if="claimReport" title="Klaim laporan?" eyebrow="PENUGASAN" :caption="shortId(claimReport.id)" @close="!claiming&&!claimUnknown&&(claimReport=null)"><p>Anda akan menjadi penanggung jawab laporan ini. Bukti dan versi resmi dapat dibaca setelah klaim berhasil.</p><p class="fine">Klaim hanya berhasil jika laporan masih tersedia.</p><ErrorNotice :error="claimError" /><p v-if="claimUnknown" class="notice warning">Respons klaim belum pasti. Periksa hasil dengan kunci dan isi permintaan yang sama sebelum melanjutkan.</p><template #actions><button :disabled="claiming||claimUnknown" @click="claimReport=null">Batal</button><button class="primary" :disabled="claiming||!online" @click="claim">{{ claiming?'Memeriksa…':claimUnknown?'Periksa hasil klaim':'Klaim laporan' }}</button></template></AppDialog>
 <AppDialog v-if="selected" title="Ringkasan administratif" eyebrow="LAPORAN RESMI" class="ws-summary-dialog" :caption="'Laporan '+shortId(selected.id)" @close="closeSummary"><FetchState v-if="summaryBusy" compact title="Memuat ringkasan laporan…" /><FetchState v-else-if="summaryError" compact state="error" title="Ringkasan belum dapat dimuat" description="Coba lagi untuk membaca laporan yang sama." :error="summaryError" @retry="readSummary" /><template v-else-if="summary"><dl class="ws-definition ws-administrative-summary"><dt>Kategori</dt><dd>{{ label(summary.report.event_type) }}</dd><dt>Versi resmi</dt><dd>{{ summary.report.official_version }}</dd><dt>Dikirim</dt><dd>{{ date(summary.report.submitted_at) }}</dd><dt>Tahap</dt><dd><WorkspaceStatus :value="summary.report.workflow_status" /></dd><dt>Penanggung jawab</dt><dd>{{ summary.assignment?.operator_name||'Belum ditugaskan' }}</dd></dl><p class="fine">Ringkasan ini tidak membuka narasi, bukti privat, atau tindakan pemeriksaan Operator.</p></template><template #actions><button v-if="canAssign&&summary&&summary.report.workflow_status!=='CLOSED'" class="primary" @click="assignment={...selected,revision:summary.report.revision,operator_id:summary.assignment?.operator_id||null,operator_name:summary.assignment?.operator_name||null};closeSummary()">Kelola penugasan</button><button @click="closeSummary">Tutup</button></template></AppDialog>
</template>
