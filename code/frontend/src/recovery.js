import {ApiError} from './api.js';

export function requiresStoredState(error) {
  return ['RESPONSE_UNKNOWN', 'REQUEST_RUNNING', 'REQUEST_UNKNOWN'].includes(error?.code);
}

export function analysisRequests(rows, reportId) {
  return rows.filter(row => row.report_id === reportId && row.scope === `POST reports/${reportId}/analyses/`);
}

export function reportRequests(rows, reportId) {
  return rows.filter(row => row.report_id === reportId);
}

export function requestAction(scope) {
  if (scope?.endsWith('/analyses/')) return 'Analisis';
  if (scope?.endsWith('/cards/revisions/')) return 'Koreksi kartu';
  if (scope?.endsWith('/narratives/revisions/')) return 'Revisi narasi';
  if (scope?.endsWith('/human-verifications/')) return 'Konfirmasi versi';
  if (scope?.endsWith('/submit/')) return 'Pengiriman laporan';
  return {'reports.create':'Pembuatan draft','evidence.upload':'Penyimpanan bukti','bundles.create':'Pembentukan bundle'}[scope] || 'Tindakan laporan';
}

export function reportRequestGuidance(record) {
  if (record?.scope?.endsWith('/analyses/')) return requestGuidance(record.state);
  return {
    RUNNING:'Permintaan masih diproses. Baca kembali keadaan tersimpan sebelum tindakan baru.',
    UNKNOWN:'Hasil tindakan belum pasti. Periksa request dan keadaan laporan sebelum melanjutkan.',
    SUCCEEDED:'Tindakan telah tersimpan. Laporan yang dibaca menampilkan keadaan terbaru, bukan snapshot lama.',
    FAILED:'Kegagalan telah tercatat. Periksa keadaan terbaru dan penyebabnya sebelum tindakan eksplisit berikutnya.',
  }[record?.state] || 'Baca keadaan laporan terbaru sebelum melanjutkan.';
}

export async function readStoredReportAction(read, reportId, key) {
  const invalid = () => new ApiError('Referensi request tidak sesuai laporan. Muat ulang keadaan tersimpan.', 'INVALID_RESPONSE');
  const request = (await read(`requests/${encodeURIComponent(key)}/`)).data;
  if (!request || request.report_id !== reportId || request.key !== key) throw invalid();
  let run = null;
  if (request.result_type === 'Run' && request.result_id) {
    if (request.scope !== `POST reports/${reportId}/analyses/`) throw invalid();
    run = (await read(`reports/${encodeURIComponent(reportId)}/analysis-runs/${encodeURIComponent(request.result_id)}/`)).data;
    if (!run || run.id !== request.result_id || run.report_id !== reportId) throw invalid();
  }
  const detail = (await read(`reports/${encodeURIComponent(reportId)}/`)).data;
  if (detail?.report?.id !== reportId) throw invalid();
  return {request, run, detail};
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
