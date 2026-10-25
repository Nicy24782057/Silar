import { reviewState } from './review.js';

// Stage access follows stored sources/results. Local progress never confirms a card.
export function reportStageAccess(detail, {pendingInput=false, editingReview=false, advancedCardId=null} = {}) {
  const report=detail?.report;
  if (!report?.id || !report.workflow_status) return {review:false,confirm:false,reviewReason:'Simpan bukti dan jalankan analisis terlebih dahulu.',confirmReason:'Periksa hasil terlebih dahulu.'};
  const state=reviewState(detail), narrative=detail.active_narrative;
  const official=state.submitted && Boolean(detail.official_card);
  const revisedNarrative=Boolean(narrative?.origin==='REPORTER_REVISION' &&
    narrative.id===report.active_narrative_id && narrative.bundle_id===report.active_bundle_id);
  const review=official || (!pendingInput && (state.current || revisedNarrative));
  const confirm=official || Boolean(review && state.current && !state.nonEvent && !editingReview &&
    (state.canSubmit || advancedCardId===detail.current_card?.id));
  const reviewReason=pendingInput?'Selesaikan perubahan input atau bukti terlebih dahulu.':
    state.held?'Tunggu hasil analisis atau periksa keadaan permintaan tersimpan.':'Simpan bukti dan jalankan analisis terlebih dahulu.';
  const confirmReason=editingReview?'Simpan atau batalkan koreksi yang masih terbuka.':
    pendingInput?'Selesaikan perubahan input atau bukti terlebih dahulu.':
    state.nonEvent?'Hasil NON_EVENT memerlukan perbaikan sumber atau narasi dan analisis ulang.':
    !state.current?'Hasil yang sesuai dengan sumber aktif belum tersedia.':'Periksa hasil, lalu tekan Lanjut ke konfirmasi pada tahap 2.';
  return {review,confirm,reviewReason:review?'':reviewReason,confirmReason:confirm?'':confirmReason};
}
