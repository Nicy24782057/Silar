<script setup>
import { computed } from 'vue';
import { label } from '../domain';
import { analysisContext, fieldLabels } from '../analysis';
import { incidentIcon } from '../report-list';
import AppIcon from './AppIcon.vue';
const props = defineProps({detail:Object,heading:String,showNarrative:{type:Boolean,default:true}});
const context = computed(() => analysisContext(props.detail));
const title = computed(() => props.heading || (props.detail?.report?.submitted_at ? 'Incident Card resmi' :
  props.detail?.current_card?.source_kind==='REPORTER_FIELD_REVISION' ? 'Incident Card hasil koreksi' : 'Draft awal Incident Card'));
const reasons = computed(() => (Array.isArray(props.detail?.current_card?.uncertain_reasons) ? props.detail.current_card.uncertain_reasons : []).map(x => x === 'LOW_CLASSIFICATION_CONFIDENCE' ? 'Keyakinan klasifikasi rendah' : x === 'EXTRACTION_AMBIGUITY' ? 'Informasi ekstraksi perlu diperiksa' : 'Informasi hasil perlu diperiksa').join(', '));
const missing = value => value===null||value===undefined||value===''||(Array.isArray(value)&&!value.length);
const category = computed(()=>props.detail?.current_card?.data?.event_type||context.value.sena?.category);
const display = value => Array.isArray(value) ? value.length ? value.join('; ') : 'Belum tersedia' : value || 'Belum tersedia';
</script>
<template>
  <section v-if="detail?.current_card" class="card incident-card" :data-category="category">
    <div class="section-heading incident-card-heading"><div><div class="eyebrow">HASIL ANALISIS TERSIMPAN</div><h2>{{ title }}</h2></div><div class="incident-heading-actions"><span class="badge">Versi {{ detail.current_card.version_number }}</span><slot name="actions" /></div></div>
    <div v-if="context.previous" class="notice" role="status">Kartu tersimpan ini belum dapat dicocokkan dengan analisis terbaru ({{ label(detail.latest_run.status) }}). Keyakinan model dan peringatan dari proses terbaru tidak digabungkan ke kartu ini.</div>
    <div class="incident-category"><span class="category-symbol"><AppIcon :name="incidentIcon(category)" :size="30" /></span><div><span class="category-caption">Kategori kejadian</span><strong>{{ label(category) }}</strong></div><span v-if="context.sena" class="confidence-label">Keyakinan model<strong>{{ (context.sena.confidence * 100).toFixed(2) }}%</strong></span></div>
    <p class="incident-score-note">Skor model bukan kepastian kejadian. Hasil tetap perlu diperiksa.</p>
    <div v-if="(detail.current_card.data?.event_type || context.sena?.category) === 'NON_EVENT'" class="notice error">Hasil model adalah NON_EVENT. Pengiriman ditahan; hasil ini bukan keputusan bahwa pelapor berbohong.</div>
    <div v-if="detail.current_card.uncertain" class="notice warning">Hasil masih memiliki ketidakpastian{{ reasons ? ': ' + reasons : '' }}.</div>
    <div v-if="context.warnings.length" class="notice warning" role="status" aria-label="Peringatan pemeriksaan hasil ekstraksi">
      <strong>Periksa kembali hasil ekstraksi</strong>
      <ul><li v-for="(warning, index) in context.warnings" :key="index">{{ warning.message }} · {{ warning.field }}.</li></ul>
      <p class="fine">Bandingkan usulan ini dengan bukti asli. Peringatan ini terpisah dari status ketidakpastian hasil.</p>
    </div>
    <dl class="incident-fields"><div v-for="(name,key) in fieldLabels" :key="key" :class="['incident-field',{'field-wide':!['location_text','time_text'].includes(key),'field-missing':missing(detail.current_card.data?.[key])}]"><dt>{{ name }}</dt><dd>{{ display(detail.current_card.data?.[key]) }}</dd></div></dl>
    <details v-if="showNarrative&&context.narrative"><summary>Baca narasi sumber analisis</summary><p class="preserve">{{ context.narrative.text }}</p></details>
    <details><summary>Rincian sumber dan model</summary><dl class="result-fields"><dt>Sumber kartu</dt><dd>{{ detail.current_card.source_kind==='REPORTER_FIELD_REVISION'?'Koreksi Reporter':'Hasil Fusion AI' }}</dd><dt>Bundle</dt><dd>{{ detail.current_card.bundle_id }}</dd><dt>Narasi</dt><dd>{{ detail.current_card.narrative_id }}</dd><dt>Aturan Fusion</dt><dd>{{ detail.current_card.fusion_version }}</dd><template v-if="context.matches"><dt>Model SENA</dt><dd>{{ detail.latest_run.sena.model_version }}</dd><dt>Model NARA</dt><dd>{{ detail.latest_run.nara.model_version }}</dd></template></dl></details>
    <p class="fine incident-awareness"><AppIcon name="info" :size="16" /> Hasil AI perlu dibandingkan dengan bukti. Keyakinan model bukan kepastian kejadian. Informasi korban yang belum tersedia tidak berarti tidak ada korban. {{ detail.report?.submitted_at?'Versi resmi sudah dikirim; pemeriksaan petugas dan publikasi adalah tahap berikutnya.':'Selesainya analisis belum berarti laporan dikirim.' }}</p>
  </section>
</template>
