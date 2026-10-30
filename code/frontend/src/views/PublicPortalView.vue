<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { publicRead, ApiError } from '../api';
import { online } from '../network';
import { label } from '../domain';
import { incidentIcon } from '../report-list';
import { publicCategories, PUBLIC_PAGE_SIZE, publicListPath, publicTitle, publicationDate } from '../publication';
import hero from '../assets/reference/portal-hero.webp';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import PublicIncidentCard from '../components/PublicIncidentCard.vue';
import PublicNavigation from '../components/PublicNavigation.vue';
import FetchState from '../components/FetchState.vue';
const q=ref(''), category=ref(''), items=ref([]), count=ref(0), page=ref(1), next=ref(null), previous=ref(null);
const busy=ref(false), loaded=ref(false), error=ref(null), counts=ref(null), countsError=ref(null);
const selected=ref(null), record=ref(null), detailBusy=ref(false), detailError=ref(null);
const applied=ref({q:'',category:''});
let sequence=0, detailSequence=0, statsSequence=0, listAbort, detailAbort, statsAbort;
const pages=computed(()=>Math.max(1,Math.ceil(count.value/PUBLIC_PAGE_SIZE)));
async function load(targetPage=1, apply=false) {
  const generation=++sequence, filters=apply?{q:q.value.trim(),category:category.value}:{...applied.value};
  listAbort?.abort(); listAbort=new AbortController();busy.value=true;error.value=null;
  try {
    const result=await publicRead(publicListPath({...filters,page:targetPage}),{signal:listAbort.signal});
    if(generation!==sequence)return;
    items.value=result.results;count.value=result.count;next.value=result.next;previous.value=result.previous;
    page.value=targetPage;applied.value=filters;loaded.value=true;
  } catch(e) {if(generation===sequence&&e.name!=='AbortError'){error.value=e;items.value=[];loaded.value=false;}}
  finally {if(generation===sequence)busy.value=false;}
}
async function loadCounts() {
  const generation=++statsSequence;statsAbort?.abort();statsAbort=new AbortController();countsError.value=null;
  try {
    const result=await Promise.all(['',...publicCategories].map(category=>publicRead(publicListPath({category,pageSize:1}),{signal:statsAbort.signal})));
    if(generation===statsSequence)counts.value=result.map(value=>value.count);
  } catch(e) {if(generation===statsSequence&&e.name!=='AbortError'){counts.value=null;countsError.value=e;}}
}
async function readDetail() {
  const id=selected.value;if(!id)return;
  const generation=++detailSequence;detailAbort?.abort();detailAbort=new AbortController();record.value=null;detailBusy.value=true;detailError.value=null;
  try {
    const result=await publicRead(`public/reports/${id}/`,{signal:detailAbort.signal});
    if(generation!==detailSequence)return;
    if(result.data.id!==id)throw new ApiError('Rincian laporan tidak sesuai. Silakan muat ulang.','INVALID_RESPONSE');
    record.value=result.data;
  } catch(e) {if(generation===detailSequence&&e.name!=='AbortError')detailError.value=e;}
  finally {if(generation===detailSequence)detailBusy.value=false;}
}
function open(item){selected.value=item.id;readDetail();}
function close(){++detailSequence;detailAbort?.abort();selected.value=null;record.value=null;detailError.value=null;}
function refresh(){load(page.value);loadCounts();}
onMounted(()=>{load();loadCounts();});
onBeforeUnmount(()=>{++sequence;++detailSequence;++statsSequence;listAbort?.abort();detailAbort?.abort();statsAbort?.abort();});
</script>
<template>
 <div class="portal-page">
  <div class="public-site-header"><PublicNavigation /></div>
  <div class="portal-content">
   <section class="portal-hero"><div><p class="eyebrow">PORTAL PUBLIK SILAR</p><h1>Informasi kejadian.<br>Terbuka untuk semua.</h1><p>Telusuri Incident Card yang telah disetujui untuk ditayangkan<br class="desktop-break"> kepada publik.</p><small><AppIcon name="globe" :size="18" />Akses informasi tanpa akun</small></div><img :src="hero" alt="" class="portal-hero-art"></section>
   <div class="public-stats" aria-label="Jumlah seluruh publikasi"><article v-for="(key,index) in ['',...publicCategories]" :key="key" :data-category="key"><div>{{ key?label(key):'Total publikasi' }}<AppIcon :name="key?incidentIcon(key):'reports'" :size="20" /></div><p><strong>{{ counts?counts[index]:'—' }}</strong> {{ key?'laporan':'laporan terbit' }}</p><small>{{ key?'Dipublikasikan':'Seluruh kategori kejadian' }}</small></article></div>
   <div v-if="countsError" class="notice warning" role="status">Ringkasan jumlah belum dapat dibaca.<button :disabled="!online" @click="loadCounts">Muat ulang ringkasan</button></div>
   <section id="publications" aria-labelledby="publications-title"><div class="publications-heading"><div><p class="eyebrow">INCIDENT CARD PUBLIK</p><h2 id="publications-title">Jelajahi laporan terbit</h2></div><span><AppIcon name="down" :size="15" />Publikasi terbaru</span></div>
    <form class="public-filters" @submit.prevent="load(1,true)"><label>Cari laporan<div class="public-search"><AppIcon name="search" :size="19" /><input v-model="q" type="search" placeholder="Cari lokasi, ringkasan, atau perkembangan" maxlength="500"></div></label><label>Kategori kejadian<select v-model="category" @change="load(1,true)"><option value="">Semua kategori</option><option v-for="key in publicCategories" :key="key" :value="key">{{ label(key) }}</option></select></label><button class="primary" :disabled="busy||!online">Cari</button></form>
    <div class="public-results-caption"><span>{{ busy?'Membaca publikasi…':loaded?`Menampilkan ${items.length} dari ${count} publikasi`:'Publikasi belum dapat dibaca' }}</span><button class="link small" :disabled="busy||!online" @click="refresh"><AppIcon name="refresh" :size="14" />Muat ulang</button></div>
    <FetchState v-if="busy" title="Memuat publikasi…" description="Membaca laporan yang telah disetujui dan diterbitkan." /><FetchState v-else-if="error" state="error" title="Publikasi belum dapat dimuat" description="Coba lagi untuk membaca publikasi terbaru." :error="error" :disabled="busy||!online" @retry="refresh" />
    <FetchState v-else-if="loaded&&!items.length" state="empty" :title="applied.q||applied.category?'Tidak ada publikasi yang sesuai':'Belum ada publikasi'" :description="applied.q||applied.category?'Ubah kata pencarian atau kategori untuk mencoba kembali.':'Laporan akan tampil setelah disetujui dan diterbitkan oleh petugas.'"><template #actions><button v-if="applied.q||applied.category" :disabled="!online" @click="q='';category='';load(1,true)">Atur ulang filter</button></template></FetchState>
    <div v-else-if="loaded" class="public-card-grid"><article v-for="item in items" :key="item.id" class="public-list-card" :data-category="item.event_type"><header><div><small>Kategori kejadian</small><h3>{{ label(item.event_type) }}</h3></div><span><AppIcon :name="incidentIcon(item.event_type)" :size="26" /></span></header><div class="public-card-body"><small><AppIcon :name="item.general_location?'pin':'reports'" :size="14" />{{ item.general_location?'Lokasi kejadian':'Identitas laporan' }}</small><h3>{{ publicTitle(item) }}</h3><p v-if="!item.general_location" class="unavailable-location">Lokasi belum tersedia</p><small><AppIcon name="clock" :size="14" />Waktu yang disebut</small><p class="public-time">{{ item.time_text||'Belum tersedia' }}</p><div class="public-card-date"><span><small>Tayang</small><time :datetime="item.published_at">{{ publicationDate(item.published_at) }}</time></span><code>#{{ item.id.slice(0,8) }}</code></div><button :aria-label="'Buka Incident Card '+item.id.slice(0,8)" @click="open(item)">Buka Incident Card<AppIcon name="arrow" :size="15" /></button></div></article></div>
    <nav v-if="loaded&&count&&!error&&!busy" class="public-pagination" aria-label="Halaman publikasi"><button :disabled="!previous||busy||!online" @click="load(page-1)">‹ Sebelumnya</button><span aria-live="polite">Halaman {{ page }} dari {{ pages }}</span><button :disabled="!next||busy||!online" @click="load(page+1)">Berikutnya ›</button></nav>
   </section>
  </div>
  <footer class="public-footer"><div><strong>SILAR</strong><p>Merangkai Informasi, Memahami Situasi.</p></div><div>Portal informasi publik<p>Sistem Inteligensi Laporan Adaptif dan Responsif</p></div></footer>
  <AppDialog v-if="selected" title="Incident Card publik" :caption="'#'+selected.slice(0,8)" @close="close"><FetchState v-if="detailBusy" compact title="Memuat rincian publikasi…" :description="'Membaca laporan #'+selected.slice(0,8)" /><FetchState v-else-if="detailError" state="error" compact title="Rincian publikasi belum dapat dimuat" description="Coba lagi untuk membaca informasi publik yang dipilih." :error="detailError" :disabled="detailBusy||!online" @retry="readDetail" /><PublicIncidentCard v-if="record" :record="record" /><template #actions><button @click="close">Tutup</button></template></AppDialog>
 </div>
</template>
