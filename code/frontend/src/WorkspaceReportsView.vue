<script setup>
import {computed,reactive,ref,watch} from 'vue';
import {useRoute,useRouter} from 'vue-router';
import {api} from '../api';
import {session} from '../session';
import {date,label,paginationPath} from '../domain';
import {hasPermission,shortId,categoryOptions,workflowOptions,workspaceReportsPath,workspaceQuickView} from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
import WorkspaceStatus from '../components/WorkspaceStatus.vue';
import WorkspaceAssignment from '../components/WorkspaceAssignment.vue';
const route=useRoute(),router=useRouter();
const scope=computed(()=>route.meta.workspaceScope||'assigned');
const quickView=computed(()=>workspaceQuickView(scope.value,route.query.view));
const titles={queue:'Antrean Laporan',assigned:'Penanganan Saya',monitor:'Monitoring Laporan',assignment:'Penugasan'};
const captions={queue:'Ringkasan laporan resmi yang belum memiliki penanggung jawab.',assigned:'Laporan yang menjadi tanggung jawab akun Anda saat ini.',monitor:'Pantau laporan resmi dan status penanganan sesuai kewenangan.',assignment:'Tetapkan penanggung jawab dan catat setiap pengalihan.'};
const filters=reactive({q:'',event_type:'',workflow_status:'',ordering:'-submitted_at'});
const rows=ref([]),count=ref(0),next=ref(null),previous=ref(null),busy=ref(false),error=ref(null),message=ref('');
const assignment=ref(null),claimReport=ref(null),claiming=ref(false);let generation=0,claimKey=null;
const canAssign=computed(()=>session.user?.role==='ADMIN'&&hasPermission(session.user,'assign_report'));
const canClaim=computed(()=>hasPermission(session.user,'claim_report')&&hasPermission(session.user,'view_assigned_report'));
async function load(path){
  const version=++generation;busy.value=true;error.value=null;
  try{const r=await api(path||workspaceReportsPath(scope.value,{...(quickView.value?.filters||{}),...filters,q:filters.q.trim().replace(/^#/, '')}));if(version!==generation)return;rows.value=r.results;count.value=r.count;next.value=r.next;previous.value=r.previous;}
  catch(e){if(version===generation){error.value=e;rows.value=[];count.value=0;next.value=null;previous.value=null;}}
  finally{if(version===generation)busy.value=false;}
}
watch([scope,()=>route.query.view],()=>{Object.assign(filters,{q:'',event_type:'',workflow_status:'',ordering:'-submitted_at'});message.value='';load();},{immediate:true});
function openClaim(row){claimReport.value=row;claimKey=crypto.randomUUID();error.value=null;}
async function claim(){
  if(claiming.value||!claimReport.value)return;claiming.value=true;error.value=null;
  try{const row=claimReport.value;await api(`workspace/reports/${row.id}/claim/`,{method:'POST',key:claimKey,body:{expected_revision:row.revision}});claimReport.value=null;await router.push('/workspace/reports/'+row.id);}
  catch(e){claimReport.value=null;await load();error.value=e;}finally{claiming.value=false;}
}
async function assigned(text){assignment.value=null;message.value=text;await load();}
</script>
<template>
 <div class="page-heading ws-page-heading"><div><div class="eyebrow">RUANG KERJA {{ session.user?.role==='ADMIN'?'ADMIN':'OPERATOR' }}</div><h1>{{ quickView?.title||titles[scope] }}</h1><p class="subtitle">{{ quickView?.caption||captions[scope] }}</p></div><button :disabled="busy" @click="load()"><AppIcon name="refresh" :size="15" />Muat ulang</button></div>
 <ErrorNotice :error="error" /><p v-if="message" class="notice success" role="status">{{ message }}</p>
 <p v-if="quickView" class="ws-quick-filter"><span><AppIcon name="search" :size="17" />Filter dashboard: {{ quickView.title }}</span><RouterLink to="/workspace/assigned">Tampilkan semua penanganan<AppIcon name="arrow" :size="15" /></RouterLink></p>
 <p class="ws-info-line"><AppIcon name="shield" :size="18" />{{ scope==='queue'?'Antrean berisi ringkasan resmi tanpa identitas Reporter atau bukti privat.':'Akses administratif tidak otomatis memberikan hak membaca bukti atau melakukan tindakan Operator.' }}</p>
 <section class="card ws-table-panel" :aria-busy="busy">
  <header class="ws-panel-heading"><div><h2>{{ scope==='assignment'?'Pengelolaan penugasan':'Daftar laporan resmi' }}</h2><p>{{ count }} laporan sesuai hak akses Anda.</p></div></header>
  <form class="ws-filters" @submit.prevent="load()"><label class="ws-search"><AppIcon name="search" :size="17" /><span class="sr-only">Cari ID laporan</span><input v-model="filters.q" placeholder="Cari ID laporan" maxlength="37"></label><label><span class="sr-only">Kategori</span><select v-model="filters.event_type" @change="load()"><option value="">Semua kategori</option><option v-for="item in categoryOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select></label><label v-if="scope!=='queue'"><span class="sr-only">Tahap laporan</span><select v-model="filters.workflow_status" @change="load()"><option value="">Semua tahap</option><option v-for="item in workflowOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select></label><label><span class="sr-only">Urutan</span><select v-model="filters.ordering" @change="load()"><option value="-submitted_at">Terbaru</option><option value="submitted_at">Terlama</option></select></label><button type="submit" :disabled="busy">Cari</button></form>
  <p v-if="busy" class="ws-loading" role="status">Membaca laporan…</p>
  <div v-if="!busy&&!rows.length" class="empty"><AppIcon name="reports" :size="36" /><h3>{{ scope==='queue'?'Antrean belum tersedia':'Belum ada laporan yang sesuai' }}</h3><p>{{ scope==='assigned'?'Laporan akan muncul setelah Anda mengklaim atau menerima penugasan dari Admin.':'Ubah filter atau muat ulang untuk memeriksa keadaan terbaru.' }}</p></div>
  <div v-if="rows.length" class="ws-table-scroll"><table class="ws-table"><thead><tr><th>Laporan</th><th>Kategori</th><th>Status</th><th v-if="scope!=='queue'">Penanggung jawab</th><th>Aksi</th></tr></thead><tbody><tr v-for="row in rows" :key="row.id"><td><strong :title="row.id">{{ shortId(row.id) }}</strong><small>{{ date(row.submitted_at) }}</small><small>Versi resmi {{ row.official_version }}</small></td><td>{{ label(row.event_type) }}</td><td><WorkspaceStatus :value="row.workflow_status" /></td><td v-if="scope!=='queue'">{{ row.operator_name||'Belum ditugaskan' }}</td><td class="ws-row-actions"><template v-if="scope==='queue'"><button class="primary small" :disabled="busy||!canClaim" @click="openClaim(row)">Klaim laporan</button><small v-if="!canClaim">Izin klaim belum diberikan</small></template><template v-else><RouterLink class="ws-text-link" :to="'/workspace/reports/'+row.id">Lihat {{ scope==='assigned'?'detail':'ringkasan' }}<AppIcon name="arrow" :size="13" /></RouterLink><button v-if="canAssign&&scope==='assignment'" class="link" :disabled="busy||row.workflow_status==='CLOSED'" @click="assignment=row">{{ row.operator_id?'Alihkan':'Tugaskan' }}</button></template></td></tr></tbody></table></div>
  <footer class="ws-pagination"><span>{{ count }} laporan</span><div><button :disabled="busy||!previous" @click="load(paginationPath(previous))">Sebelumnya</button><button :disabled="busy||!next" @click="load(paginationPath(next))">Berikutnya</button></div></footer>
 </section>
 <WorkspaceAssignment v-if="assignment" :report="assignment" @close="assignment=null" @saved="assigned" />
 <AppDialog v-if="claimReport" title="Klaim laporan?" :caption="shortId(claimReport.id)" @close="!claiming&&(claimReport=null)"><p>Anda akan menjadi penanggung jawab laporan ini. Bukti dan versi resmi dapat dibaca setelah klaim berhasil.</p><p class="fine">Klaim hanya berhasil jika laporan masih tersedia.</p><template #actions><button :disabled="claiming" @click="claimReport=null">Batal</button><button class="primary" :disabled="claiming" @click="claim">{{ claiming?'Mengklaim…':'Klaim laporan' }}</button></template></AppDialog>
</template>
