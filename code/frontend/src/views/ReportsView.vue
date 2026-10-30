<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue';
import { api, ApiError } from '../api';
import { online } from '../network';
import { label, paginationPath } from '../domain';
import { reportsPath, statusFilters, categoryFilters, reportStatus, reportStatuses, REPORT_PAGE_SIZE, incidentIcon } from '../report-list';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import ReportStatus from '../components/ReportStatus.vue';
import ReportCardPreview from '../components/ReportCardPreview.vue';
import FetchState from '../components/FetchState.vue';
import DeleteDraftDialog from '../components/DeleteDraftDialog.vue';
const deleting=ref(null),deleteMessage=ref('');
function deleted(){deleting.value=null;closeDetail();deleteMessage.value='Laporan yang belum dikirim telah dihapus.';load(reportsPath(loadedFilters.value.status,loadedFilters.value.order,loadedFilters.value.category,1),true);loadCounts();}

const items = ref([]), count = ref(0), next = ref(null), previous = ref(null);
const busy = ref(false), error = ref(null), loaded = ref(false), refreshedAt = ref(null);
const status = ref(''), category = ref(''), order = ref('-created_at');
const loadedFilters = ref({status:'',category:'',order:'-created_at'}), loadedPath = ref(reportsPath());
const selected = ref(null), detail = ref(null), detailBusy = ref(false), detailError = ref(null), showStatuses = ref(false);
const counts = ref(null), countsError = ref(null), countsBusy=ref(false);
const officialStates=['SUBMITTED','ASSIGNED','IN_REVIEW','FOLLOW_UP','CLOSED'];
const segmentColors=['#155EBD','#289DBF','#8B68BD','#119C96','#2E986D'];
let listSequence = 0, detailSequence = 0, countsSequence=0;
const officialCount=computed(()=>counts.value?officialStates.reduce((sum,key)=>sum+counts.value[key],0):null);
const metrics=computed(()=>[
 ['Total laporan',counts.value?.total,'Semua laporan milik Anda','reports'],
 ['Belum dikirim',counts.value?.NOT_SUBMITTED,'Masih dalam persiapan Anda','edit'],
 ['Dalam penanganan',counts.value?officialCount.value-counts.value.CLOSED:null,'Laporan resmi yang belum ditutup','search'],
 ['Penanganan ditutup',counts.value?.CLOSED,'Baca keputusan pada rincian','check']
]);
async function loadCounts(){
 const generation=++countsSequence;countsBusy.value=true;countsError.value=null;
 try{
  const states=['total','NOT_SUBMITTED',...officialStates];
  const results=await Promise.all(states.map(key=>api('reports/?'+new URLSearchParams({scope:'owned',page_size:'1',...(key==='total'?{}:{workflow_status:key})}))));
  if(generation===countsSequence)counts.value=Object.fromEntries(states.map((key,index)=>[key,results[index].count]));
 }catch(e){if(generation===countsSequence){counts.value=null;countsError.value=e;}}
 finally{if(generation===countsSequence)countsBusy.value=false;}
}
function refreshAll(){load(loadedPath.value,true);loadCounts();}
const activePage = computed(() => Number(new URL(loadedPath.value,'http://localhost/').searchParams.get('page') || 1));
const pages = computed(() => Math.max(1,Math.ceil(count.value / REPORT_PAGE_SIZE)));
const pageNumbers = computed(() => {
  const start = Math.max(1,Math.min(activePage.value-2,pages.value-4));
  return Array.from({length:Math.min(5,pages.value)},(_,i)=>start+i);
});
const filtered = computed(() => Boolean(loadedFilters.value.status || loadedFilters.value.category));
const previewOfficial = computed(() => Boolean(detail.value?.report.submitted_at || (detail.value && detail.value.report.workflow_status !== 'NOT_SUBMITTED')));
const previewAction = computed(() => previewOfficial.value ? 'Lihat rincian' : !detail.value?.current_card ? 'Lanjutkan laporan' : detail.value.report.preparation_status === 'BLOCKED' ? 'Perbaiki laporan' : 'Edit');
const dateFormatter = new Intl.DateTimeFormat('id-ID',{dateStyle:'medium'});
const timeFormatter = new Intl.DateTimeFormat('id-ID',{timeStyle:'short'});
const formatDate = value => value ? dateFormatter.format(new Date(value)) : 'Belum tersedia';
const formatTime = value => value ? timeFormatter.format(new Date(value)) : '';

async function load(path, refreshing = false) {
  const sequence = ++listSequence;
  const requested = {status:status.value,category:category.value,order:order.value};
  const target = path || reportsPath(requested.status,requested.order,requested.category);
  busy.value = true; error.value = null;
  if (!refreshing) refreshedAt.value = null;
  try {
    const result = await api(target);
    if (sequence !== listSequence) return;
    items.value = result.results; count.value = result.count; next.value = result.next; previous.value = result.previous;
    loadedFilters.value = requested; loadedPath.value = target; loaded.value = true;
    if (refreshing) refreshedAt.value = new Intl.DateTimeFormat('id-ID',{timeStyle:'medium'}).format(new Date());
  } catch (e) {
    if (sequence !== listSequence) return;
    error.value = e;
    ({status:status.value,category:category.value,order:order.value} = loadedFilters.value);
  } finally { if (sequence === listSequence) busy.value = false; }
}
function resetFilters() { status.value='';category.value='';load(); }
function goPage(page) { load(reportsPath(loadedFilters.value.status,loadedFilters.value.order,loadedFilters.value.category,page)); }
async function readDetail() {
  const item = selected.value; if (!item) return;
  const sequence = ++detailSequence;
  detailBusy.value = true; detailError.value = null; detail.value = null;
  try {
    const result = await api('reports/'+item.id+'/');
    if (sequence !== detailSequence) return;
    if (result?.data?.report?.id !== item.id) throw new ApiError('Rincian tidak sesuai dengan laporan yang dipilih. Muat ulang untuk memeriksa kembali.','INVALID_RESPONSE');
    detail.value = result.data;
  } catch (e) { if (sequence === detailSequence) detailError.value = e; }
  finally { if (sequence === detailSequence) detailBusy.value = false; }
}
function openDetail(item) { selected.value=item;readDetail(); }
function closeDetail() { ++detailSequence;selected.value=null;detail.value=null;detailError.value=null;detailBusy.value=false; }
onMounted(() => {load();loadCounts();});
onBeforeUnmount(() => { ++listSequence;++detailSequence;++countsSequence; });
</script>
<template>
  <div class="page-heading reports-heading"><div><div class="eyebrow">RUANG REPORTER</div><h1>Laporan Saya</h1><p class="subtitle">Ringkasan laporan Anda dan perkembangan penanganan.</p></div><span class="page-private"><AppIcon name="lock" :size="14" /> Laporan pribadi Anda</span></div>
  <p v-if="deleteMessage" class="notice success" role="status">{{ deleteMessage }}</p>
  <div class="reporter-metrics" :aria-busy="countsBusy"><article v-for="[title,value,note,icon] in metrics" :key="title" class="reporter-metric"><h2>{{ title }}</h2><AppIcon :name="icon" :size="20" /><strong>{{ value??'—' }}</strong><small>{{ note }}</small></article></div>
  <div v-if="countsError" class="notice warning" role="status">Ringkasan seluruh laporan belum dapat dibaca.<button :disabled="countsBusy||!online" @click="loadCounts">Muat ulang ringkasan</button></div>
  <section class="card reporter-distribution" aria-labelledby="report-status-title">
    <header><div><h2 id="report-status-title">Sebaran laporan resmi</h2><p>Jumlah pada setiap status saat ini; bukan urutan waktu.</p></div><span>{{ officialCount??'—' }} laporan</span></header>
    <div class="reporter-distribution-body"><div class="distribution-bar" aria-hidden="true"><span v-for="(key,index) in officialStates" :key="key" :style="{'--segment':segmentColors[index],flex:counts?counts[key]:1}"></span></div><div class="distribution-counts"><div v-for="(key,index) in officialStates" :key="key" :style="{'--segment':segmentColors[index]}"><p><i></i>{{ reportStatuses[key].label }}</p><strong>{{ counts?counts[key]:'—' }}</strong><small>laporan</small></div></div></div>
  </section>
  <section class="card reports-table-card" :aria-busy="busy" aria-labelledby="report-list-title">
    <div class="report-list-toolbar">
      <div class="report-list-title"><h2 id="report-list-title">Daftar laporan</h2></div><button class="small report-status-help" @click="showStatuses=true"><AppIcon name="info" :size="16" />Arti warna & status</button>
      <div class="report-list-controls">
        <label class="report-select"><span class="sr-only">Status laporan</span><select v-model="status" aria-label="Status laporan" :disabled="busy||!online" @change="load()"><option v-for="item in statusFilters" :key="item.value" :value="item.value">{{ item.label }}</option></select><AppIcon name="down" :size="14" /></label>
        <label class="report-select"><span class="sr-only">Kategori laporan</span><select v-model="category" aria-label="Kategori laporan" :disabled="busy||!online" @change="load()"><option v-for="item in categoryFilters" :key="item.value" :value="item.value">{{ item.label }}</option></select><AppIcon name="down" :size="14" /></label>
        <label class="report-select"><span class="sr-only">Urutkan laporan</span><select v-model="order" aria-label="Urutkan laporan" :disabled="busy||!online" @change="load()"><option value="-created_at">Terbaru</option><option value="created_at">Terlama</option></select><AppIcon name="down" :size="14" /></label>
        <button class="report-list-reload" :disabled="busy||!online" @click="refreshAll"><AppIcon name="refresh" :size="14" />{{ busy?'Memuat…':'Muat ulang' }}</button>
      </div>
    </div>
    <div class="report-list-caption"><p>{{ loaded?count+' laporan':'Membaca daftar laporan Anda' }}</p><p v-if="refreshedAt" role="status">Dimuat ulang · {{ refreshedAt }}</p><span v-else>Hanya laporan milik Anda</span></div>
    <FetchState v-if="busy" title="Memuat daftar laporan…" description="Membaca laporan sesuai akun dan filter yang dipilih." />
    <FetchState v-else-if="error" state="error" title="Daftar laporan belum dapat dimuat" description="Coba lagi untuk membaca laporan tersimpan. Kegagalan pembacaan berbeda dari status analisis laporan." :error="error" :disabled="busy||!online" @retry="refreshAll" />
    <FetchState v-else-if="loaded&&!items.length" state="empty" :title="filtered?'Tidak ada laporan yang sesuai':'Belum ada laporan'" :description="filtered?'Pilih kategori atau status lain untuk menemukan laporan Anda.':'Buat draft pertama dan simpan bukti yang Anda ketahui.'"><template #actions><button v-if="filtered" :disabled="!online" @click="resetFilters">Atur ulang filter</button><RouterLink v-else class="button primary" to="/reports/new">Buat laporan</RouterLink></template></FetchState>
    <div v-else class="report-table-wrap" tabindex="0" role="region" aria-label="Tabel daftar laporan, dapat digeser mendatar">
      <table class="reports-table"><thead><tr><th scope="col">Laporan</th><th scope="col">Kategori</th><th scope="col">Tanggal</th><th scope="col">Tahap & pengiriman</th><th scope="col"><span class="sr-only">Tindakan</span></th></tr></thead>
        <tbody><tr v-for="item in items" :key="item.id">
          <td><div class="report-reference"><span class="report-file-symbol"><AppIcon :name="incidentIcon(item.event_type)" :size="18" /></span><span><strong class="report-id">#{{ item.id.slice(0,8) }}</strong><small>{{ item.preparation_status==='DRAFT'?'Draft laporan':'Laporan tersimpan' }}</small></span></div></td>
          <td class="report-category">{{ item.event_type==='EARTHQUAKE'?'Gempa Bumi':item.event_type?label(item.event_type):item.preparation_status==='DRAFT'?'Belum dianalisis':'Belum terklasifikasi' }}</td>
          <td class="report-date"><time :datetime="item.created_at">{{ formatDate(item.created_at) }}<small>{{ formatTime(item.created_at) }}</small></time></td>
          <td><div class="report-stage"><ReportStatus :status="reportStatus(item)" compact /><span class="report-stage-note">{{ item.workflow_status==='NOT_SUBMITTED'?'Belum dikirim':item.workflow_status==='SUBMITTED'?'Menunggu Operator':'Laporan resmi' }}</span><span v-if="item.uncertain" class="report-uncertain"><AppIcon name="alert" :size="12" />Tidak pasti</span></div></td>
          <td class="report-table-action"><button class="report-detail-button" :aria-label="'Detail laporan '+item.id.slice(0,8)" @click="openDetail(item)">Detail <AppIcon name="arrow" :size="14" /></button><button v-if="item.workflow_status==='NOT_SUBMITTED'&&!item.submitted_at" class="link small report-delete-button" :aria-label="'Hapus laporan '+item.id.slice(0,8)" :disabled="busy||!online" @click="deleting=item">Hapus</button></td>
        </tr></tbody>
      </table>
    </div>
    <nav v-if="loaded&&!error&&!busy" class="report-pages" aria-label="Halaman daftar laporan">
      <p class="report-page-caption" aria-live="polite">{{ count&&items.length?'Menampilkan '+((activePage-1)*REPORT_PAGE_SIZE+1)+'–'+((activePage-1)*REPORT_PAGE_SIZE+items.length)+' dari '+count+' laporan':'0 laporan' }}</p>
      <div class="report-page-buttons">
        <button :disabled="!previous||busy||!online" @click="load(paginationPath(previous))">‹ Sebelumnya</button>
        <span v-if="pageNumbers[0]>1" aria-hidden="true">…</span>
        <button v-for="page in pageNumbers" :key="page" :aria-label="'Halaman '+page" :aria-current="activePage===page?'page':undefined" :disabled="busy||!online" @click="goPage(page)">{{ page }}</button>
        <span v-if="pageNumbers.at(-1)<pages" aria-hidden="true">…</span>
        <button :disabled="!next||busy||!online" @click="load(paginationPath(next))">Berikutnya ›</button>
      </div>
    </nav>
  </section>
  <p class="list-privacy-note"><AppIcon name="lock" :size="15" /> Selesainya analisis belum berarti laporan dikirim. Periksa hasil dan konfirmasikan versi yang tepat sebelum pengiriman resmi.</p>

  <AppDialog v-if="selected" :title="detail&&!detail.current_card&&!previewOfficial?'Ringkasan Draft':'Incident Card'" :caption="'LAPORAN #'+selected.id.slice(0,8)" @close="closeDetail">
    <FetchState v-if="detailBusy" compact title="Memuat rincian laporan…" :description="'Membaca laporan #'+selected.id.slice(0,8)" /><FetchState v-else-if="detailError" state="error" compact title="Rincian laporan belum dapat dimuat" description="Coba lagi untuk membaca kartu dan keadaan terbaru." :error="detailError" :disabled="!online||detailBusy" @retry="readDetail" />
    <ReportCardPreview v-if="detail" :detail="detail" />
    <template #actions><button class="secondary" @click="closeDetail">Tutup</button><RouterLink v-if="detail" class="button primary" :to="'/reports/'+detail.report.id">{{ previewAction }}</RouterLink></template>
  </AppDialog>
  <AppDialog v-if="showStatuses" title="Arti warna & status" caption="STATUS LAPORAN" @close="showStatuses=false">
    <ul class="report-status-help-list"><li v-for="(value,key) in reportStatuses" :key="key"><ReportStatus :status="value" /><p>{{ value.description }}</p></li></ul>
    <p class="notice">Warna menunjukkan tahap proses. uncertain dan NON_EVENT merupakan kondisi hasil AI tersendiri. Penutupan proses tidak membuktikan semua informasi benar atau kejadian sudah terselesaikan.</p>
    <template #actions><button @click="showStatuses=false">Tutup</button></template>
  </AppDialog>
  <DeleteDraftDialog v-if="deleting" :report="deleting" @close="deleting=null" @deleted="deleted" @refresh="refreshAll" />
</template>
