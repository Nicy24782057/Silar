<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue';
import { api } from '../api';
import { date, paginationPath } from '../domain';
import { online } from '../network';
import { session } from '../session';
import { refreshUnread, notificationState } from '../notifications';
import { roleLabel } from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
import FetchState from '../components/FetchState.vue';
const rows=ref([]),next=ref(null),count=ref(0),busy=ref(false),reading=ref(null),error=ref(null),message=ref(''),unread=ref(false);
const loadError=ref(null);let sequence=0;
onBeforeUnmount(()=>{sequence++;});
async function load(path){
  const generation=++sequence;busy.value=true;loadError.value=null;
  try{const result=await api(path||('notifications/'+(unread.value?'?unread=true':'')));if(generation!==sequence)return;rows.value=path?[...rows.value,...result.results]:result.results;next.value=result.next;count.value=result.count;}
  catch(e){if(generation===sequence)loadError.value=e;}finally{if(generation===sequence)busy.value=false;}
}
async function mark(item){
  reading.value=item.id;error.value=null;message.value='';
  try{const result=await api(`notifications/${item.id}/read/`,{method:'PATCH',body:{}});
    if(unread.value)await load();else rows.value=rows.value.map(row=>row.id===item.id?result.data:row);
    message.value='Notifikasi ditandai sudah dibaca.';refreshUnread();
  }catch(e){error.value=e;}finally{reading.value=null;}
}
onMounted(()=>{load();refreshUnread();});
</script>
<template>
  <div class="page-heading"><div><div class="eyebrow">RUANG {{ roleLabel(session.user?.role).toUpperCase() }}</div><h1>Notifikasi</h1><p class="subtitle">Ikuti perubahan laporan dan informasi yang relevan dengan akun Anda.</p></div><span class="page-private"><AppIcon name="lock" :size="14" />{{ session.user?.role==='REPORTER'?'Ruang privat':'Sesuai kewenangan' }}</span></div>
  <section class="notification-banner"><div><h2>{{ session.user?.role==='ADMIN'?'Pembaruan akun, dalam satu tempat.':session.user?.role==='OPERATOR'?'Perkembangan penanganan, dalam satu tempat.':'Perkembangan laporan, dalam satu tempat.' }}</h2><p>{{ session.user?.role==='ADMIN'?'Buka ringkasan laporan untuk membaca keadaan terbaru.':'Buka laporan untuk membaca keadaan terbaru. Menandai notifikasi dibaca tidak mengubah status laporan.' }}</p></div><div class="notification-banner-count"><AppIcon name="bell" :size="32" /><strong>{{ notificationState.unread??'—' }}</strong><small>belum dibaca</small></div></section>
  <div class="notification-toolbar"><div class="notification-filters" aria-label="Filter notifikasi"><button :aria-pressed="!unread" :disabled="busy||!online" @click="unread=false;load()">Semua notifikasi</button><button :aria-pressed="unread" :disabled="busy||!online" @click="unread=true;load()">Belum dibaca</button></div><span>{{ notificationState.unread===null?'Jumlah belum tersedia':notificationState.unread+' belum dibaca' }}</span><button :disabled="busy||!online" @click="load();refreshUnread()"><AppIcon name="refresh" :size="15" />Muat ulang</button></div>
  <ErrorNotice :error="error" /><div v-if="message" class="notice success" role="status">{{ message }}</div>
  <section class="card notification-card" aria-labelledby="notification-list-title" :aria-busy="busy">
    <div class="section-heading notification-heading"><h2 id="notification-list-title">{{ session.user?.role==='ADMIN'?'Aktivitas akun':'Aktivitas laporan' }}</h2><span>{{ busy?'Membaca notifikasi…':loadError?'Jumlah belum tersedia':count+' notifikasi' }}</span></div>
    <FetchState v-if="busy" title="Memuat notifikasi…" description="Membaca aktivitas yang relevan dengan akun Anda." compact />
    <FetchState v-else-if="loadError" state="error" title="Notifikasi belum dapat dimuat" description="Coba lagi untuk membaca pembaruan tersimpan." :error="loadError" compact :disabled="busy||!online" @retry="load()" />
    <FetchState v-else-if="!rows.length" state="empty" icon="bell" compact :title="unread?'Tidak ada notifikasi yang belum dibaca':'Belum ada notifikasi'" description="Pembaruan tersedia ketika ada tindakan yang relevan."><template #actions><button v-if="unread" @click="unread=false;load()">Tampilkan semua notifikasi</button></template></FetchState>
    <ul v-else class="notification-list">
      <li v-for="item in rows" :key="item.id" class="notification-item" :class="{'is-unread':!item.read_at}">
        <span class="heading-icon"><AppIcon name="bell" :size="16" /></span>
        <div class="notification-body">
          <p class="notification-message">{{ item.message }}</p>
          <div class="notification-meta">
            <span v-if="item.report_id">#{{ item.report_id.slice(0,8) }} ·</span><time :datetime="item.created_at">{{ date(item.created_at) }}</time>
            <span class="notification-read-state" :class="{'notification-unread':!item.read_at}"><i aria-hidden="true" />{{ item.read_at?'Sudah dibaca':'Belum dibaca' }}</span>
          </div>
        </div>
        <div class="notification-actions">
          <RouterLink v-if="item.report_id&&session.user?.role==='REPORTER'" :to="'/reports/'+item.report_id">Buka laporan<AppIcon name="arrow" :size="13" /></RouterLink>
          <RouterLink v-else-if="item.report_id" :to="'/workspace/reports/'+item.report_id">Buka laporan<AppIcon name="arrow" :size="13" /></RouterLink>
          <button v-if="!item.read_at" class="link" :disabled="busy||reading!==null||!online" @click="mark(item)">{{ reading===item.id?'Menandai…':'Tandai dibaca' }}</button>
        </div>
      </li>
    </ul>
    <div v-if="next&&!loadError&&!busy" class="notification-pagination"><button class="full" :disabled="busy||!online" @click="load(paginationPath(next))">Muat notifikasi berikutnya</button></div>
    <p class="notification-footer"><AppIcon name="info" :size="15" />Notifikasi mencatat aktivitas saat itu. Rincian laporan menampilkan keadaan terkini.</p>
  </section><p class="fine">Status baca dan status penanganan laporan memiliki fungsi yang berbeda.</p>
</template>
