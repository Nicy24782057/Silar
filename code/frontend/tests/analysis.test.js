import test from 'node:test';
import assert from 'node:assert/strict';
import {analysisContext} from '../src/analysis.js';
function fixture(uncertain = false) {
  return {current_card:{bundle_id:'bundle',narrative_id:'narrative',sena_result_id:'sena',nara_result_id:'nara',uncertain},
    latest_run:{id:'run',bundle_id:'bundle',status:'SUCCEEDED',
      sena:{id:'sena',analysis_run_id:'run',narrative_id:'narrative',confidence:0.98},
      nara:{id:'nara',analysis_run_id:'run',narrative_id:'narrative',normalization_warnings:[{code:'INFORMATION_AS_IMPACT_SUGGESTION',field:'impacts'}]}},
    active_narrative:{id:'narrative',text:'Bukti sumber'}};
}
test('Peringatan tampil ketika uncertain false tanpa mengubah flag', () => {
  const detail = fixture();
  assert.equal(analysisContext(detail).warnings[0].message, 'Usulan dampak perlu diperiksa');
  assert.equal(detail.current_card.uncertain, false);
});
test('Peringatan dan uncertain true tetap terpisah', () => {
  const detail = fixture(true);
  assert.equal(analysisContext(detail).warnings.length, 1);
  assert.equal(detail.current_card.uncertain, true);
});
test('Kode baru memakai pesan umum dan label field aman', () => {
  const detail = fixture();
  detail.latest_run.nara.normalization_warnings = [{code:'constructor',field:'toString'}];
  assert.deepEqual(analysisContext(detail).warnings, [{message:'Informasi hasil ekstraksi perlu diperiksa',field:'Informasi kejadian'}]);
});
test('Hasil kosong dan NARA yang belum tersedia aman', () => {
  for (const detail of [null,{}, {latest_run:null}, {current_card:fixture().current_card,latest_run:{status:'RUNNING',nara:null}}]) assert.deepEqual(analysisContext(detail).warnings, []);
  const detail = fixture(); detail.latest_run.nara.normalization_warnings = [];
  assert.deepEqual(analysisContext(detail).warnings, []);
});
test('Analisis terbaru gagal tidak memasangkan peringatan/keyakinannya ke kartu lama', () => {
  const detail = fixture(); detail.latest_run.status = 'FAILED';
  const result = analysisContext(detail);
  assert.equal(result.previous, true); assert.equal(result.sena, null); assert.deepEqual(result.warnings, []);
});
test('Identitas run, hasil, bundle, dan narasi harus cocok', () => {
  for (const change of [d=>d.current_card.nara_result_id='old',d=>d.latest_run.bundle_id='new',d=>d.latest_run.nara.analysis_run_id='other',d=>d.latest_run.sena.narrative_id='other']) {
    const detail = fixture(); change(detail); assert.equal(analysisContext(detail).matches, false);
  }
});
test('Narasi baru tidak dilabeli sebagai sumber kartu lama', () => {
  const detail = fixture(); detail.active_narrative = {id:'new',text:'Sumber lain'};
  assert.equal(analysisContext(detail).narrative, null);
  detail.latest_run.output_narrative = {id:'narrative',text:'Sumber sesuai'};
  assert.equal(analysisContext(detail).narrative.text, 'Sumber sesuai');
});
