<script setup>
import {onMounted,ref} from 'vue';
import {api} from '../api';
import {date} from '../domain';
import AppIcon from '../components/AppIcon.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
const data=ref(null),busy=ref(false),error=ref(null);
async function load(){busy.value=true;error.value=null;try{data.value=(await api('workspace/services/')).data;}catch(e){error.value=e;data.value=null;}finally{busy.value=false;}}
onMounted(load);
</script>
<template>
 <div class="page-heading ws-page-heading"><div><div class="eyebrow">PEMANTAUAN SISTEM</div><h1>Monitoring Layanan</h1><p class="subtitle">Baca status dan metadata terukur tanpa mengubah proses analisis.</p></div><button :disabled="busy" @click="load"><AppIcon name="refresh" :size="15" />Muat ulang</button></div>
 <ErrorNotice :error="error" /><p v-if="busy" class="ws-loading" role="status">Memeriksa layanan…</p>
 <template v-if="data"><p class="ws-info-line"><AppIcon name="shield" :size="18" />Terakhir diperiksa {{ date(data.checked_at) }}. Metadata berasal dari layanan dan proses yang tercatat.</p>
 <div class="ws-stat-grid ws-stat-grid-three"><section class="card ws-stat"><div><span>Database</span><AppIcon name="server" /></div><strong>{{ data.database==='READY'?'Tersedia':'Belum tersedia' }}</strong><small>Uji koneksi baca</small></section><section class="card ws-stat"><div><span>Waktu respons database</span><AppIcon name="clock" /></div><strong>{{ data.database_response_ms }} ms</strong><small>Pengukuran pada pemeriksaan ini</small></section><section class="card ws-stat"><div><span>Analisis aktif</span><AppIcon name="chart" /></div><strong>{{ data.running }} proses</strong><small>Kapasitas {{ data.analysis_capacity }} proses</small></section></div>
 <section class="card ws-table-panel"><header class="ws-panel-heading"><div><h2>Metadata proses analisis</h2><p>Jumlah proses, bukan isi laporan atau keluaran privat.</p></div></header><div class="ws-table-scroll"><table class="ws-table"><thead><tr><th>Pengukuran</th><th>Jumlah</th><th>Keterangan</th></tr></thead><tbody><tr><td>Berhasil dalam 24 jam</td><td>{{ data.succeeded_24h }}</td><td>Proses tercatat selesai</td></tr><tr><td>Gagal dalam 24 jam</td><td>{{ data.failed_24h }}</td><td>Memerlukan pemeriksaan sesuai prosedur teknis</td></tr><tr><td>Hasil belum pasti</td><td>{{ data.unknown }}</td><td>Keadaan proses belum terminal</td></tr><tr><td>Melewati tenggat awal</td><td>{{ data.overdue }}</td><td>Pemulihan mengikuti prosedur pengelola teknis</td></tr></tbody></table></div><p class="ws-panel-foot"><AppIcon name="lock" :size="15" />Halaman ini hanya baca. Pemantauan tidak membuka draft Reporter atau menjalankan ulang analisis.</p></section>
 </template>
</template>
