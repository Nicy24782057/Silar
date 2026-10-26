<script setup>
import {computed,onMounted,ref} from 'vue';
import {RouterLink} from 'vue-router';
import {api} from '../api';
import {session} from '../session';
import {date,label} from '../domain';
import {shortId,roleLabel,dashboardCardLink,ADMIN_REPORTS_PATH,ADMIN_REPORTS_TITLE} from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
import WorkspaceStatus from '../components/WorkspaceStatus.vue';
const data=ref(null),busy=ref(false),error=ref(null);
const admin=computed(()=>session.user?.role==='ADMIN');
const cards=computed(()=>{const n=data.value?.counts||{};return (admin.value?[
  ['official','Laporan resmi','Seluruh laporan yang sudah dikirim','reports'],['unassigned','Belum ditugaskan','Memerlukan penanggung jawab','clipboard'],
  ['operators','Operator aktif','Akun aktif dan terverifikasi','users'],['closed','Laporan ditutup','Riwayat tetap tersedia','check']]:[
  ['queue','Antrean dapat diklaim','Siap untuk Anda tangani','reports'],['assigned','Dalam penanganan','Laporan aktif saat ini','clipboard'],
  ['review_pending','Perlu direview','Menunggu pemeriksaan petugas','check'],['followup_pending','Tindak lanjut pending','Memerlukan tindak lanjut','clock']])
  .map(([key,title,caption,icon])=>({key,title,caption,icon,value:n[key],unit:key==='operators'?'akun':'laporan',to:n[key]===undefined?null:dashboardCardLink(session.user,key),action:{official:'Lihat laporan resmi',unassigned:'Lihat belum ditugaskan',operators:'Lihat Operator aktif',closed:'Lihat laporan ditutup',queue:'Buka antrean',assigned:'Lihat penanganan',review_pending:'Buka daftar review',followup_pending:'Lihat tindak lanjut'}[key]}));});
const scopeTo=computed(()=>({queue:'/workspace/queue',assigned:'/workspace/assigned',monitor:ADMIN_REPORTS_PATH,assignment:ADMIN_REPORTS_PATH}[data.value?.scope]));
const scopeAction=computed(()=>['monitor','assignment'].includes(data.value?.scope)?ADMIN_REPORTS_TITLE:'Lihat laporan');
async function load(){busy.value=true;error.value=null;try{data.value=(await api('workspace/dashboard/')).data;}catch(e){error.value=e;data.value=null;}finally{busy.value=false;}}
onMounted(load);
</script>
<template>
  <div class="page-heading ws-page-heading"><div><div class="eyebrow">SISTEM INFORMASI LAPORAN</div><h1>Dashboard {{ roleLabel(session.user?.role) }}</h1><p class="subtitle">Selamat datang, {{ session.user?.full_name }}. {{ admin?'Pantau laporan resmi dan penugasan sesuai kewenangan.':'Tinjau antrean dan tangani laporan yang menjadi tanggung jawab Anda.' }}</p></div><button :disabled="busy" @click="load"><AppIcon name="refresh" :size="15" />Muat ulang</button></div>
  <ErrorNotice :error="error" />
  <p v-if="$route.query.denied" class="notice warning">Halaman tersebut memerlukan kewenangan yang belum diberikan kepada akun Anda.</p>
  <section class="ws-hero"><div><div class="eyebrow">RUANG KERJA {{ roleLabel(session.user?.role).toUpperCase() }}</div><h2>Setiap laporan, langkah menuju perubahan.</h2><p>{{ admin?'Pantau laporan dan pastikan penugasan berjalan dengan baik.':'Tinjau antrean, tangani laporan, dan catat tindak lanjut yang tepat.' }}</p><RouterLink v-if="scopeTo" class="button primary" :to="scopeTo">{{ scopeAction }}<AppIcon name="arrow" :size="17" /></RouterLink></div><div class="ws-hero-art" aria-hidden="true"><div class="ws-document"><AppIcon name="reports" :size="28" /><strong>LAPORAN RESMI</strong><i/><i/><div><b>Tercatat. Tertangani.</b><small>Pelayanan yang lebih baik.</small></div><i/></div><span><AppIcon name="check" :size="28" /></span></div></section>
  <p v-if="busy" class="ws-loading" role="status">Memuat ringkasan ruang kerja…</p>
  <div class="ws-stat-grid"><component :is="card.to?RouterLink:'section'" v-for="(card,index) in cards" :key="card.key" :to="card.to||undefined" class="ws-stat ws-metric card" :class="['ws-metric-'+index,{'ws-metric-link':card.to}]" :aria-label="card.to?card.title+': '+card.value+' '+card.unit+'. '+card.action:undefined"><div><span>{{ card.title }}</span><span class="ws-stat-icon" :class="'accent-'+index"><AppIcon :name="card.icon" :size="21" /></span></div><strong>{{ card.value??'—' }}</strong><small>{{ card.value===undefined?'Memerlukan izin terkait':card.caption }}</small><span v-if="card.to" class="ws-metric-action">{{ card.action }}<AppIcon name="arrow" :size="17" /></span></component></div>
  <div class="ws-dashboard-grid"><section class="card ws-table-panel"><header class="ws-panel-heading"><div><h2>{{ admin?'Laporan terbaru':'Laporan resmi terbaru' }}</h2><p>Ringkasan laporan dalam kewenangan Anda.</p></div><RouterLink v-if="scopeTo" :to="scopeTo" class="ws-text-link">Lihat semua <AppIcon name="arrow" :size="14" /></RouterLink></header>
    <div v-if="!busy&&!data?.reports?.length" class="empty"><AppIcon name="reports" :size="36" /><h3>Belum ada laporan resmi</h3><p>Laporan akan muncul setelah Reporter mengirim versi resminya dan sesuai izin akun Anda.</p></div>
    <div v-else class="ws-table-scroll"><table class="ws-table"><thead><tr><th>ID laporan</th><th>Kategori</th><th>Status</th><th>{{ data?.scope==='queue'?'Aksi':'Penanggung jawab' }}</th></tr></thead><tbody><tr v-for="report in data?.reports||[]" :key="report.id"><td><RouterLink v-if="data?.scope!=='queue'" :to="'/workspace/reports/'+report.id">{{ shortId(report.id) }}</RouterLink><strong v-else>{{ shortId(report.id) }}</strong><small>{{ date(report.submitted_at) }}</small></td><td>{{ label(report.event_type) }}</td><td><WorkspaceStatus :value="report.workflow_status" /></td><td><RouterLink v-if="data?.scope==='queue'" class="ws-text-link" to="/workspace/queue">Buka antrean</RouterLink><span v-else>{{ report.operator_name||'Belum ditugaskan' }}</span></td></tr></tbody></table></div>
    <p class="ws-panel-foot"><AppIcon name="shield" :size="15" />Detail privat hanya tersedia sesuai penugasan dan izin.</p>
  </section><section class="card ws-activity"><h2>Aktivitas terkini</h2><p v-if="!data?.activities?.length" class="muted">Belum ada pembaruan untuk akun ini.</p><ol><li v-for="item in data?.activities||[]" :key="item.id"><span class="heading-icon"><AppIcon name="bell" :size="17" /></span><div><p>{{ item.message }}</p><small>{{ date(item.created_at) }}</small></div></li></ol><RouterLink class="ws-text-link" to="/notifications">Lihat notifikasi<AppIcon name="arrow" :size="14" /></RouterLink></section></div>
</template>
