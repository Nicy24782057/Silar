<script setup>
import { onMounted, ref } from 'vue';
import { api } from '../api';
import { date, paginationPath } from '../domain';
import { online } from '../network';
import { session } from '../session';
import { roleLabel } from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
const rows=ref([]),next=ref(null),count=ref(0),busy=ref(false),reading=ref(null),error=ref(null),message=ref(''),unread=ref(false);
async function load(path){
  busy.value=true;error.value=null;
  try{const result=await api(path||('notifications/'+(unread.value?'?unread=true':'')));rows.value=path?[...rows.value,...result.results]:result.results;next.value=result.next;count.value=result.count;}
  catch(e){error.value=e;}finally{busy.value=false;}
}
async function mark(item){
  reading.value=item.id;error.value=null;message.value='';
  try{const result=await api(`notifications/${item.id}/read/`,{method:'PATCH',body:{}});
    if(unread.value)await load();else rows.value=rows.value.map(row=>row.id===item.id?result.data:row);
    message.value='Notifikasi ditandai sudah dibaca.';
  }catch(e){error.value=e;}finally{reading.value=null;}
}
onMounted(()=>load());
</script>
<template>
  <div class="page-heading"><div><div class="eyebrow">RUANG {{ roleLabel(session.user?.role).toUpperCase() }}</div><h1>Notifikasi</h1><p class="subtitle">Perubahan yang relevan dengan laporan dan kewenangan akunmu.</p></div><button :disabled="busy||!online" @click="load()"><AppIcon name="refresh" :size="15" />Muat ulang</button></div>
  <ErrorNotice :error="error" /><div v-if="message" class="notice success" role="status">{{ message }}</div>
  <section class="card notification-card" aria-labelledby="notification-list-title" :aria-busy="busy">
    <div class="section-heading notification-heading">
      <h2 id="notification-list-title">{{ count }} notifikasi</h2>
      <label class="check-label"><input v-model="unread" type="checkbox" :disabled="busy||!online" @change="load()">Hanya belum dibaca</label>
    </div>
    <p v-if="busy" class="notification-loading" role="status">Membaca notifikasi…</p>
    <div v-else-if="!rows.length" class="empty"><h3>Belum ada notifikasi{{ unread?' yang belum dibaca':'' }}</h3><p>Pembaruan tersedia ketika ada tindakan yang relevan.</p></div>
    <ul class="notification-list">
      <li v-for="item in rows" :key="item.id" class="notification-item" :class="{'is-unread':!item.read_at}">
        <span class="heading-icon"><AppIcon name="bell" :size="16" /></span>
        <div class="notification-body">
          <p class="notification-message">{{ item.message }}</p>
          <div class="notification-meta">
            <time :datetime="item.created_at">{{ date(item.created_at) }}</time>
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
    <div v-if="next" class="notification-pagination"><button class="full" :disabled="busy||!online" @click="load(paginationPath(next))">Muat notifikasi berikutnya</button></div>
  </section><p class="fine">Notifikasi membantu mengikuti laporan Anda. Buka rincian untuk membaca keadaan terbaru sebelum melakukan tindakan.</p>
</template>
