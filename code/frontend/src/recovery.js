import {ApiError} from './api.js';

export function requiresStoredState(error) {
  return ['RESPONSE_UNKNOWN', 'REQUEST_RUNNING', 'REQUEST_UNKNOWN'].includes(error?.code);
}

export function analysisRequests(rows, reportId) {
  return rows.filter(row => row.report_id === reportId && row.scope === `POST reports/${reportId}/analyses/`);
}

export function requestGuidance(state) {
  return {
    RUNNING: 'Analisis masih diproses. Baca kembali status; jangan kirim analisis kedua.',
    UNKNOWN: 'Hasil penyimpanan belum dapat dipastikan. Analisis baru ditahan sampai pemulihan teknis selesai.',
    SUCCEEDED: 'Analisis telah tersimpan. Hasil pada halaman ini mengikuti sumber draft terbaru.',
    FAILED: 'Analisis berakhir dengan kegagalan yang tercatat. Periksa penyebab dan sumber terbaru sebelum mencoba lagi secara eksplisit.',
  }[state] || 'Baca keadaan draft terbaru sebelum melakukan tindakan berikutnya.';
}

export async function readStoredAnalysis(read, reportId, key) {
  const invalid = () => new ApiError('Referensi hasil tidak sesuai dengan draft ini. Muat ulang halaman.', 'INVALID_RESPONSE');
  const request = (await read(`requests/${encodeURIComponent(key)}/`)).data;
  if (!request || request.report_id !== reportId || request.key !== key ||
    request.scope !== `POST reports/${reportId}/analyses/`) throw invalid();
  let run = null;
  if (request.result_type === 'Run' && request.result_id) {
    run = (await read(`reports/${encodeURIComponent(reportId)}/analysis-runs/${encodeURIComponent(request.result_id)}/`)).data;
    if (!run || run.id !== request.result_id || run.report_id !== reportId) throw invalid();
  }
  const detail = (await read(`reports/${encodeURIComponent(reportId)}/`)).data;
  if (detail?.report?.id !== reportId) throw invalid();
  return {request, run, detail};
}
