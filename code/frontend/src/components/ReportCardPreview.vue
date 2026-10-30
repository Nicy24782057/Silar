<script setup>
import { computed } from 'vue';
import { label } from '../domain';
import { analysisContext, fieldLabels } from '../analysis';
import { reportStatus, incidentIcon } from '../report-list';
import AppIcon from './AppIcon.vue';
import ReportStatus from './ReportStatus.vue';
const props = defineProps({ detail: { type: Object, required: true } });
const submitted = computed(() => Boolean(props.detail.report.submitted_at || props.detail.report.workflow_status !== 'NOT_SUBMITTED'));
const card = computed(() => submitted.value ? props.detail.official_card : props.detail.current_card);
const projection = computed(() => ({ ...props.detail, current_card: card.value }));
const context = computed(() => analysisContext(projection.value));
const category = computed(() => card.value?.data?.event_type || context.value.sena?.category);
const display = value => Array.isArray(value) ? value.length ? value.join('; ') : 'Belum tersedia' : value || 'Belum tersedia';
const missing = value => value == null || value === '' || (Array.isArray(value) && value.length === 0);
</script>
<template>
  <div class="preview-state"><ReportStatus :status="reportStatus(detail.report)" /><span v-if="card">Kartu versi {{ card.version_number }}<template v-if="submitted"> · Versi resmi terkunci</template></span></div>
  <template v-if="card">
    <div class="preview-category" :data-category="category"><span class="heading-icon"><AppIcon :name="incidentIcon(category)" :size="24" /></span><div><p>Kategori kejadian</p><h3>{{ category === 'EARTHQUAKE' ? 'Gempa Bumi' : label(category) }}</h3><small v-if="context.sena">Keyakinan model {{ (Number(context.sena.confidence)*100).toLocaleString('id-ID',{maximumFractionDigits:2}) }}%</small></div></div>
    <p v-if="submitted" class="notice">Versi resmi telah dikirim dan terkunci. Rincian serta riwayat tetap dapat dibaca.</p>
    <p v-else class="notice">Bandingkan hasil AI dengan bukti sebelum konfirmasi dan pengiriman melalui halaman rincian.</p>
    <p v-if="category === 'NON_EVENT'" class="notice warning">NON_EVENT: input belum diklasifikasikan sebagai kejadian yang dapat dikirim. Perbaiki sumber atau narasi melalui rincian laporan.</p>
    <p v-if="card.uncertain" class="notice warning">uncertain · Hasil masih memiliki ketidakpastian. Baca alasan serta sumber pada rincian laporan sebelum melanjutkan.</p>
    <p v-if="context.previous" class="notice">Skor dan peringatan analisis terbaru tidak digabungkan karena referensinya berbeda dari kartu ini.</p>
    <div v-if="context.warnings.length" class="notice warning"><strong>Periksa hasil ekstraksi</strong><ul><li v-for="(warning,index) in context.warnings" :key="index">{{ warning.message }} · {{ warning.field }}.</li></ul></div>
    <dl class="preview-fields"><div v-for="(name,key) in fieldLabels" :key="key"><dt>{{ name }}</dt><dd :class="{'preview-missing':missing(card.data?.[key])}">{{ display(card.data?.[key]) }}</dd></div></dl>
    <details v-if="context.narrative"><summary>Narasi sumber</summary><p class="preserve">{{ context.narrative.text }}</p></details>
    <details><summary>Referensi kartu</summary><dl class="result-fields"><dt>Bundle</dt><dd>{{ card.bundle_id }}</dd><dt>Narasi</dt><dd>{{ card.narrative_id }}</dd><dt>Sumber kartu</dt><dd>{{ card.source_kind === 'REPORTER_FIELD_REVISION' ? 'Koreksi Reporter' : 'Hasil Fusion AI' }}</dd><dt>Versi Fusion</dt><dd>{{ card.fusion_version }}</dd></dl></details>
  </template>
  <div v-else class="empty preview-empty"><AppIcon name="file" :size="32" /><h3>{{ submitted ? 'Versi resmi belum dapat dibaca' : 'Incident Card belum tersedia' }}</h3><p>{{ submitted ? 'Buka rincian untuk memeriksa keadaan laporan terbaru.' : 'Lanjutkan draft untuk melengkapi bukti dan membaca hasil analisis yang tersimpan.' }}</p></div>
</template>
