<script setup>
import { computed } from 'vue';
import { label } from '../domain';
import { reportStatus } from '../report-list';
import ReportStatus from './ReportStatus.vue';
const props=defineProps({detail:{type:Object,required:true},sourceCount:Number});
const submitted=computed(()=>Boolean(props.detail.report.submitted_at||props.detail.report.workflow_status!=='NOT_SUBMITTED'));
const bundle=computed(()=>submitted.value?props.detail.official_bundle:props.detail.active_bundle);
const card=computed(()=>submitted.value?props.detail.official_card:props.detail.current_card);
const channels=computed(()=>[...new Set((bundle.value?.items||[]).map(x=>x.evidence.type))]);
</script>
<template>
  <section class="card report-summary">
    <h2>{{ submitted?'Ringkasan laporan':'Ringkasan draft' }}</h2>
    <dl class="summary-fields">
      <div><dt>Nomor laporan</dt><dd>#{{ detail.report.id.slice(0,8) }}</dd></div>
      <div><dt>Pengiriman</dt><dd>{{ submitted?'Sudah dikirim':'Belum dikirim' }}</dd></div>
      <div><dt>{{ submitted?'Bukti resmi':'Bukti aktif' }}</dt><dd>{{ sourceCount ?? bundle?.items.length ?? 0 }} item</dd></div>
      <div><dt>{{ submitted?'Versi resmi':'Versi kartu aktif' }}</dt><dd>{{ card?'v'+card.version_number:'Belum tersedia' }}</dd></div>
      <div v-if="card?.data?.event_type"><dt>Kategori</dt><dd>{{ label(card.data.event_type) }}</dd></div>
    </dl>
    <ReportStatus :status="reportStatus(detail.report)" />
    <div v-if="sourceCount===undefined&&channels.length" class="channel-list"><span v-for="type in channels" :key="type" class="channel">{{ {TEXT:'Teks',AUDIO:'Audio',IMAGE:'Gambar'}[type] }}</span></div>
  </section>
</template>
