<script setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api';
import { date, label, paginationPath } from '../domain';
import ErrorNotice from '../components/ErrorNotice.vue';
const router=useRouter(); const items=ref([]); const count=ref(0); const next=ref(null); const previous=ref(null);
const busy=ref(false); const error=ref(null); const unknownCreate=ref(false);
async function load(path='reports/?scope=owned&ordering=-created_at') {
  busy.value=true; error.value=null;
  try { const result=await api(path); items.value=result.results; count.value=result.count; next.value=result.next; previous.value=result.previous; unknownCreate.value=false; }
  catch(e){error.value=e;} finally{busy.value=false;}
}
async function create() {
  busy.value=true; error.value=null;
  try { const result=await api('reports/', {method:'POST', body:{}, key:crypto.randomUUID()}); await router.push('/reports/'+result.data.report.id); }
  catch(e){error.value=e; if(e.code==='RESPONSE_UNKNOWN') unknownCreate.value=true;} finally{busy.value=false;}
}
onMounted(()=>load());
</script>
<template>
  <div class="page-heading"><div><div class="eyebrow">RUANG REPORTER</div><h1>Laporan Saya</h1><p class="subtitle">Lanjutkan draft dan temukan bukti yang sudah kamu simpan.</p></div><button class="primary" :disabled="busy || unknownCreate" @click="create">＋ Buat Laporan</button></div>
  <ErrorNotice :error="error" />
  <div class="card"><div class="section-heading"><div><h2>Daftar laporan</h2><p class="muted">{{ count }} laporan milikmu</p></div><button class="small" :disabled="busy" @click="load()">Muat ulang</button></div>
    <div v-if="busy" class="empty" role="status">Membaca laporan…</div>
    <div v-else-if="!items.length" class="empty"><span class="empty-icon" aria-hidden="true">▤</span><h3>Belum ada laporan</h3><p>Buat draft pertama. Bukti yang berhasil disimpan akan tetap tersedia ketika kamu kembali.</p></div>
    <ul v-else class="report-list"><li v-for="item in items" :key="item.id"><div class="report-title"><RouterLink :to="'/reports/'+item.id">{{ item.event_type?label(item.event_type):'Draft laporan' }} <span class="muted">#{{ item.id.slice(0,8) }}</span></RouterLink><small>{{ date(item.created_at) }}</small></div><div class="report-status"><span class="badge" :class="item.preparation_status.toLowerCase()">{{ label(item.preparation_status) }}</span><small>{{ label(item.workflow_status) }}</small></div><RouterLink class="open-link" :to="'/reports/'+item.id">Buka <span aria-hidden="true">→</span></RouterLink></li></ul>
    <div v-if="next || previous" class="pagination"><button :disabled="!previous || busy" @click="load(paginationPath(previous))">← Sebelumnya</button><button :disabled="!next || busy" @click="load(paginationPath(next))">Berikutnya →</button></div>
  </div>
  <p class="fine">Daftar menampilkan ringkasan. Isi laporan dan media privat diambil ketika kamu membukanya.</p>
</template>
