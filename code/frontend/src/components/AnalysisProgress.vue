<script setup>
import {useId} from 'vue';
const headingId=useId();
import AppIcon from './AppIcon.vue';
defineProps({state:{type:Object,required:true}});
</script>
<template>
 <section v-if="state.visible" class="card analysis-progress-panel" :class="'analysis-'+state.outcome" :aria-labelledby="headingId">
  <header><span class="analysis-orbit" aria-hidden="true"><AppIcon :name="state.outcome==='complete'?'check':['failed','unknown'].includes(state.outcome)?'alert':'shield'" :size="26" /></span><div><p class="eyebrow">ANALISIS LAPORAN</p><h2 :id="headingId">{{ state.outcome==='complete'?'Analisis selesai':state.outcome==='failed'?'Analisis belum berhasil':state.outcome==='unknown'?'Hasil analisis perlu dipastikan':'Laporan Anda sedang dianalisis' }}</h2><p role="status">{{ ['failed','unknown'].includes(state.outcome)?'Periksa keadaan tersimpan sebelum menjalankan analisis lagi.':state.outcome==='preparing'?'Menyiapkan bukti untuk analisis…':state.label }}</p></div><strong class="analysis-percentage">{{ state.percent }}<small>%</small></strong></header>
  <div class="analysis-progress-track" role="progressbar" aria-label="Tahapan analisis selesai" :aria-valuenow="state.percent" aria-valuemin="0" aria-valuemax="100" :aria-valuetext="state.completed+' dari '+state.total+' tahap selesai'"><span :style="{width:state.percent+'%'}"></span></div>
  <p class="analysis-progress-caption">{{ state.completed }} dari {{ state.total }} tahap selesai · Waktu setiap tahap dapat berbeda.</p>
  <ol class="analysis-stage-list"><li v-for="step in state.steps" :key="step.key" :class="step.state" :aria-current="step.state==='current'?'step':undefined"><span><AppIcon v-if="step.state==='done'" name="check" :size="12" /><i v-else /></span>{{ step.label }}</li></ol>
  <p v-if="state.readError&&!['failed','unknown'].includes(state.outcome)" class="analysis-read-warning" role="status">Progres terbaru belum dapat dibaca. Angka menunjukkan keadaan terakhir yang berhasil diterima.</p>
 </section>
</template>
