<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue';
import { api, ApiError } from '../api';
import { online } from '../network';
import { label, paginationPath } from '../domain';
import { reportsPath, statusFilters, categoryFilters, reportStatus, reportStatuses, legendStatuses, REPORT_PAGE_SIZE, incidentIcon } from '../report-list';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import ReportStatus from '../components/ReportStatus.vue';
import ReportCardPreview from '../components/ReportCardPreview.vue';
import ErrorNotice from '../components/ErrorNotice.vue';

const items = ref([]), count = ref(0), next = ref(null), previous = ref(null);
const busy = ref(false), error = ref(null), loaded = ref(false), refreshedAt = ref(null);
const status = ref(''), category = ref(''), order = ref('-created_at');
const loadedFilters = ref({status:'',category:'',order:'-created_at'}), loadedPath = ref(reportsPath());
const selected = ref(null), detail = ref(null), detailBusy = ref(false), detailError = ref(null), showStatuses = ref(false);
let listSequence = 0, detailSequence = 0;
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
onMounted(() => load());
onBeforeUnmount(() => { ++listSequence;++detailSequence; });
</script>
<template>
  <div class="page-heading reports-heading"><div><div class="eyebrow">RUANG REPORTER</div><h1>Laporan Saya</h1><p class="subtitle">Lanjutkan draft, periksa hasil, dan ikuti laporan yang sudah Anda kirim.</p></div><span class="page-private"><AppIcon name="lock" :size="14" /> Laporan pribadi Anda</span></div>
  <section class="card status-guide" aria-labelledby="report-status-title">
    <div><h2 id="report-status-title">Kenali tahap laporan Anda</h2>
    <div class="status-guide-badges"><ReportStatus v-for="key in legendStatuses" :key="key" :status="reportStatuses[key]" /></div></div>
    <button class="status-guide-help link" @click="showStatuses=true">Tentang status laporan <AppIcon name="chevron" :size="13" /></button>
  </section>
  <ErrorNotice :error="error" />
  <section class="card reports-table-card" :aria-busy="busy" aria-labelledby="report-list-title">
    <div class="report-list-toolbar">
      <div class="report-list-title"><span class="heading-icon"><AppIcon name="reports" :size="20" /></span><h2 id="report-list-title">Daftar Laporan</h2></div>
      <div class="report-list-controls">
        <label class="report-select"><span class="sr-only">Status laporan</span><select v-model="status" aria-label="Status laporan" :disabled="busy||!online" @change="load()"><option v-for="item in statusFilters" :key="item.value" :value="item.value">{{ item.label }}</option></select><AppIcon name="down" :size="14" /></label>
        <label class="report-select"><span class="sr-only">Kategori laporan</span><select v-model="category" aria-label="Kategori laporan" :disabled="busy||!online" @change="load()"><option v-for="item in categoryFilters" :key="item.value" :value="item.value">{{ item.label }}</option></select><AppIcon name="down" :size="14" /></label>
        <label class="report-select"><span class="sr-only">Urutkan laporan</span><select v-model="order" aria-label="Urutkan laporan" :disabled="busy||!online" @change="load()"><option value="-created_at">Terbaru</option><option value="created_at">Terlama</option></select><AppIcon name="down" :size="14" /></label>
        <button class="report-list-reload" :disabled="busy||!online" @click="load(loadedPath,true)"><AppIcon name="refresh" :size="14" />{{ busy?'Memuat…':'Muat ulang' }}</button>
      </div>
    </div>
    <div class="report-list-caption"><p>{{ loaded?count+' laporan':'Membaca daftar laporan Anda' }}</p><p v-if="refreshedAt" role="status">Dimuat ulang · {{ refreshedAt }}</p><span v-else>Hanya laporan milik Anda</span></div>
    <div v-if="busy" class="report-list-loading" role="status"><AppIcon name="clock" :size="19" /> Membaca laporan…</div>
    <div v-else-if="!loaded" class="empty"><h3>Laporan belum dapat dibaca</h3><p>Periksa pesan di atas, lalu gunakan Muat ulang untuk mencoba kembali.</p></div>
    <div v-else-if="!items.length" class="empty"><h3>{{ filtered?'Tidak ada laporan yang sesuai':'Belum ada laporan' }}</h3><p>{{ filtered?'Pilih kategori atau status lain untuk menemukan laporanmu.':'Buat draft pertama dan simpan bukti yang kamu ketahui.' }}</p><button v-if="filtered" :disabled="!online" @click="resetFilters">Tampilkan semua laporan</button><RouterLink v-else class="button primary" to="/reports/new">Buat Laporan</RouterLink></div>
    <div v-else class="report-table-wrap">
      <table class="reports-table"><thead><tr><th scope="col">Laporan</th><th scope="col">Kategori</th><th scope="col">Tanggal</th><th scope="col">Tahap & pengiriman</th><th scope="col"><span class="sr-only">Tindakan</span></th></tr></thead>
        <tbody><tr v-for="item in items" :key="item.id">
          <td><div class="report-reference"><span class="report-file-symbol"><AppIcon :name="incidentIcon(item.event_type)" :size="18" /></span><span><strong class="report-id">#{{ item.id.slice(0,8) }}</strong><small>{{ item.preparation_status==='DRAFT'?'Draft laporan':'Laporan tersimpan' }}</small></span></div></td>
          <td class="report-category">{{ item.event_type==='EARTHQUAKE'?'Gempa Bumi':item.event_type?label(item.event_type):item.preparation_status==='DRAFT'?'Belum dianalisis':'Belum terklasifikasi' }}</td>
          <td class="report-date"><time :datetime="item.created_at">{{ formatDate(item.created_at) }}<small>{{ formatTime(item.created_at) }}</small></time></td>
          <td><div class="report-stage"><ReportStatus :status="reportStatus(item)" compact /><span class="report-stage-note">{{ item.workflow_status==='NOT_SUBMITTED'?'Belum dikirim':item.workflow_status==='SUBMITTED'?'Menunggu Operator':'Laporan resmi' }}</span><span v-if="item.uncertain" class="report-uncertain"><AppIcon name="alert" :size="12" />Tidak pasti</span></div></td>
          <td class="report-table-action"><button class="report-detail-button" :aria-label="'Detail laporan '+item.id.slice(0,8)" @click="openDetail(item)">Detail <AppIcon name="arrow" :size="14" /></button></td>
        </tr></tbody>
      </table>
    </div>
    <nav v-if="loaded" class="report-pages" aria-label="Halaman daftar laporan">
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
    <p v-if="detailBusy" role="status" class="preview-loading">Membaca hasil tersimpan…</p>
    <ErrorNotice :error="detailError" />
    <button v-if="detailError" :disabled="!online||detailBusy" @click="readDetail">Muat ulang rincian</button>
    <ReportCardPreview v-if="detail" :detail="detail" />
    <template #actions><button class="secondary" @click="closeDetail">Tutup</button><RouterLink v-if="detail" class="button primary" :to="'/reports/'+detail.report.id">{{ previewAction }}</RouterLink></template>
  </AppDialog>
  <AppDialog v-if="showStatuses" title="Arti warna & status" caption="STATUS LAPORAN" @close="showStatuses=false">
    <ul class="report-status-help-list"><li v-for="(value,key) in reportStatuses" :key="key"><ReportStatus :status="value" /><p>{{ value.description }}</p></li></ul>
    <p class="notice">Warna menunjukkan tahap proses. uncertain dan NON_EVENT merupakan kondisi hasil AI tersendiri. Penutupan proses tidak membuktikan semua informasi benar atau kejadian sudah terselesaikan.</p>
    <template #actions><button @click="showStatuses=false">Tutup</button></template>
  </AppDialog>
</template>
