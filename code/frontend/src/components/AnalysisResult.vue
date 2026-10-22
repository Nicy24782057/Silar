<script setup>
import { computed } from 'vue';
import { label } from '../domain';
import { analysisContext, fieldLabels } from '../analysis';
const props = defineProps({detail: Object});
const context = computed(() => analysisContext(props.detail));
const reasons = computed(() => (Array.isArray(props.detail?.current_card?.uncertain_reasons) ? props.detail.current_card.uncertain_reasons : []).map(x => x === 'LOW_CLASSIFICATION_CONFIDENCE' ? 'Keyakinan klasifikasi rendah' : x === 'EXTRACTION_AMBIGUITY' ? 'Informasi ekstraksi perlu diperiksa' : 'Informasi hasil perlu diperiksa').join(', '));
const display = value => Array.isArray(value) ? value.length ? value.join('; ') : 'Belum tersedia' : value || 'Belum tersedia';
</script>
<template>
  <section v-if="detail?.current_card" class="card">
    <div class="section-heading"><div><div class="eyebrow">HASIL ANALISIS TERSIMPAN</div><h2>Draft awal Incident Card</h2></div><span class="badge">Versi {{ detail.current_card.version_number }}</span></div>
    <div v-if="context.previous" class="notice" role="status">Kartu tersimpan ini belum dapat dicocokkan dengan analisis terbaru ({{ label(detail.latest_run.status) }}). Keyakinan model dan peringatan dari proses terbaru tidak digabungkan ke kartu ini.</div>
    <div class="result-category"><strong>{{ label(detail.current_card.data?.event_type || context.sena?.category) }}</strong><span v-if="context.sena">Keyakinan model {{ (context.sena.confidence * 100).toFixed(2) }}%</span></div>
    <div v-if="(detail.current_card.data?.event_type || context.sena?.category) === 'NON_EVENT'" class="notice error">Hasil model adalah NON_EVENT. Pengiriman ditahan; hasil ini bukan keputusan bahwa pelapor berbohong.</div>
    <div v-if="detail.current_card.uncertain" class="notice warning">Hasil masih memiliki ketidakpastian{{ reasons ? ': ' + reasons : '' }}.</div>
    <div v-if="context.warnings.length" class="notice warning" role="status" aria-label="Peringatan pemeriksaan hasil ekstraksi">
      <strong>Periksa kembali hasil ekstraksi</strong>
      <ul><li v-for="(warning, index) in context.warnings" :key="index">{{ warning.message }} · {{ warning.field }}.</li></ul>
      <p class="fine">Bandingkan usulan ini dengan bukti asli. Peringatan ini terpisah dari status ketidakpastian hasil.</p>
    </div>
    <dl class="result-fields"><template v-for="(name, key) in fieldLabels" :key="key"><dt>{{ name }}</dt><dd>{{ display(detail.current_card.data?.[key]) }}</dd></template></dl>
    <details v-if="context.narrative"><summary>Baca narasi sumber analisis</summary><p class="preserve">{{ context.narrative.text }}</p></details>
    <p class="fine">Hasil AI perlu dibandingkan dengan bukti. Keyakinan model bukan kepastian kejadian. Informasi korban yang belum tersedia tidak berarti tidak ada korban. Selesainya analisis belum berarti laporan dikirim.</p>
  </section>
</template>
