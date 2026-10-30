<script setup>
import {ref} from 'vue';
import {label} from '../domain';
import AppIcon from './AppIcon.vue';
import AppDialog from './AppDialog.vue';
import FetchState from './FetchState.vue';
defineProps({detail:{type:Object,required:true}});
const raw=ref(null);
const fields={location_text:'Lokasi',time_text:'Waktu yang disebut',impacts:'Dampak',occurred_at:'Waktu pasti',victims:'Informasi korban',affected_objects:'Objek terdampak',involved_parties:'Pihak terlibat'};
const show=value=>Array.isArray(value)?value.length?value.join('; '):'Belum tersedia':value||'Belum tersedia';
const percent=value=>new Intl.NumberFormat('id-ID',{minimumFractionDigits:2,maximumFractionDigits:2}).format(value*100)+'%';
</script>
<template>
 <section class="card ws-ai-narrative"><header class="ws-tone-heading"><div class="eyebrow">SUMBER PEMERIKSAAN</div><h2>Narasi resmi</h2></header><div class="ws-tone-body"><p class="preserve ws-source-text">{{ detail.official_narrative?.text||'Narasi belum tersedia.' }}</p><p class="fine">Narasi ini dikirim Reporter sebagai bagian dari versi resmi {{ detail.report.official_version }}.</p></div></section>
 <div class="ws-ai-model-grid">
  <section class="card ws-model-card" :data-category="detail.ai?.sena?.category"><header class="ws-tone-heading"><h2>SENA</h2><p>Klasifikasi kategori kejadian</p></header><div v-if="detail.ai?.sena" class="ws-tone-body"><div class="ws-model-category"><span class="heading-icon"><AppIcon :name="detail.ai.sena.category==='FLOOD'?'waves':detail.ai.sena.category==='FIRE'?'flame':detail.ai.sena.category==='ACCIDENT'?'car':'pulse'" :size="26" /></span><strong>{{ label(detail.ai.sena.category) }}</strong></div><p class="ws-model-confidence">Keyakinan model<strong>{{ percent(detail.ai.sena.confidence) }}</strong></p><p class="fine">Nilai model menjadi bahan pemeriksaan petugas.</p><button class="link" @click="raw='sena'"><AppIcon name="arrow" :size="14" />Lihat keluaran mentah SENA</button></div><FetchState v-else compact state="empty" title="Hasil SENA belum tersedia" description="Hasil dibaca dari sumber versi resmi." /></section>
  <section class="card ws-model-card"><header class="ws-tone-heading"><h2>NARA</h2><p>Detail yang diekstrak dari narasi.</p></header><div v-if="detail.ai?.nara" class="ws-tone-body"><dl class="incident-fields"><div v-for="(name,key) in fields" :key="key" class="incident-field"><dt>{{ name }}</dt><dd>{{ show(detail.ai.nara.normalized_output?.[key]) }}</dd></div></dl><button class="link" @click="raw='nara'"><AppIcon name="arrow" :size="14" />Lihat keluaran mentah NARA</button></div><FetchState v-else compact state="empty" title="Hasil NARA belum tersedia" description="Informasi yang belum tersedia tidak diisi dengan asumsi." /></section>
 </div><p class="fine">Hasil AI tersimpan tetap utuh. Review petugas tidak mengganti narasi atau keluaran model.</p>
 <AppDialog v-if="raw&&detail.ai?.[raw]" :title="'Keluaran mentah '+raw.toUpperCase()" eyebrow="SUMBER PEMERIKSAAN" class="ws-model-dialog" :caption="'Versi resmi '+detail.report.official_version" @close="raw=null"><dl class="ws-definition"><dt>Model</dt><dd>{{ detail.ai[raw].model_version }}</dd></dl><pre class="ws-json">{{ JSON.stringify(detail.ai[raw].raw_output,null,2) }}</pre><template #actions><button @click="raw=null">Tutup</button></template></AppDialog>
</template>
