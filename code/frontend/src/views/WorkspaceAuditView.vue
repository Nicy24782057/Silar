<script setup>
import {onMounted,reactive,ref} from 'vue';
import {api} from '../api';
import {date,paginationPath} from '../domain';
import {eventLabels,shortId,roleLabel} from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
const rows=ref([]),count=ref(0),next=ref(null),previous=ref(null),busy=ref(false),error=ref(null),detail=ref(null);
const filters=reactive({action:'',report_id:''});
async function load(path){busy.value=true;error.value=null;try{const q=new URLSearchParams({page_size:'10'});if(filters.action)q.set('action',filters.action);if(filters.report_id.trim())q.set('report_id',filters.report_id.trim());const r=await api(path||'workspace/audit/?'+q);rows.value=r.results;count.value=r.count;next.value=r.next;previous.value=r.previous;}catch(e){error.value=e;rows.value=[];}finally{busy.value=false;}}
onMounted(()=>load());
</script>
<template>
 <div class="page-heading ws-page-heading"><div><div class="eyebrow">RIWAYAT TINDAKAN</div><h1>Audit Aktivitas</h1><p class="subtitle">Baca jejak pengelolaan sesuai kewenangan akun Anda.</p></div><button :disabled="busy" @click="load()"><AppIcon name="refresh" :size="15" />Muat ulang</button></div>
 <ErrorNotice :error="error" /><p class="ws-info-line"><AppIcon name="shield" :size="18" />Catatan audit hanya dapat dibaca. Aktor, waktu, objek, dan metadata perubahan tetap dipertahankan.</p>
 <section class="card ws-table-panel"><form class="ws-filters" @submit.prevent="load()"><label><span class="sr-only">Tindakan</span><select v-model="filters.action" @change="load()"><option value="">Semua tindakan</option><option v-for="(name,key) in eventLabels" :key="key" :value="key">{{ name }}</option></select></label><label class="ws-search"><AppIcon name="search" :size="17" /><span class="sr-only">ID lengkap laporan</span><input v-model="filters.report_id" placeholder="ID lengkap laporan (opsional)"></label><button type="submit" :disabled="busy">Terapkan</button></form>
 <p v-if="busy" class="ws-loading" role="status">Membaca audit…</p><div v-if="!busy&&!rows.length" class="empty"><h3>Belum ada catatan yang sesuai</h3><p>Ubah filter atau tunggu tindakan pengelolaan berikutnya.</p></div>
 <div v-if="rows.length" class="ws-table-scroll"><table class="ws-table"><thead><tr><th>Waktu</th><th>Aktor</th><th>Tindakan</th><th>Objek</th><th>Rincian</th></tr></thead><tbody><tr v-for="item in rows" :key="item.id"><td>{{ date(item.created_at) }}</td><td><strong>{{ item.actor_name }}</strong><small>{{ roleLabel(item.actor_role) }}</small></td><td>{{ eventLabels[item.action]||item.action }}</td><td><strong>{{ item.object_type }}</strong><small>{{ shortId(item.object_id) }}</small></td><td><button class="link" @click="detail=item">Buka rincian</button></td></tr></tbody></table></div>
 <footer class="ws-pagination"><span>{{ count }} catatan</span><div><button :disabled="busy||!previous" @click="load(paginationPath(previous))">Sebelumnya</button><button :disabled="busy||!next" @click="load(paginationPath(next))">Berikutnya</button></div></footer>
 </section>
 <AppDialog v-if="detail" title="Rincian audit" :caption="eventLabels[detail.action]||detail.action" @close="detail=null"><dl class="ws-definition"><dt>Aktor</dt><dd>{{ detail.actor_name }} / {{ roleLabel(detail.actor_role) }}</dd><dt>Waktu</dt><dd>{{ date(detail.created_at) }}</dd><dt>Objek</dt><dd>{{ detail.object_type }} / {{ detail.object_id }}</dd><dt>ID laporan</dt><dd>{{ detail.report_id||'Tidak terkait laporan' }}</dd><dt>ID bantuan</dt><dd>{{ detail.request_id }}</dd></dl><h3>Sebelum perubahan</h3><pre class="ws-json">{{ JSON.stringify(detail.before,null,2) }}</pre><h3>Setelah perubahan</h3><pre class="ws-json">{{ JSON.stringify(detail.after,null,2) }}</pre><template #actions><button @click="detail=null">Tutup</button></template></AppDialog>
</template>
