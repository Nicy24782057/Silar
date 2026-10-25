import { label } from './domain.js';

export const REPORT_PAGE_SIZE = 5;
export const categoryFilters = Object.freeze([
  { value: '', label: 'Kategori' },
  ...['FLOOD', 'EARTHQUAKE', 'FIRE', 'ACCIDENT'].map(value => ({
    value, label: value === 'EARTHQUAKE' ? 'Gempa Bumi' : label(value),
  })),
  { value: 'UNCLASSIFIED', label: 'Tanpa kategori' },
]);

// One definition for list badges, filters and the status explanation.
export const reportStatuses = Object.freeze({
  DRAFT: { label: 'Draft', icon: 'edit', tone: 'draft', preparation: 'DRAFT',
    description: 'Laporan masih dipersiapkan dan belum dikirim.' },
  PROCESSING: { label: 'Sedang dianalisis', icon: 'clock', tone: 'sent', preparation: 'PROCESSING',
    description: 'Analisis sedang diproses. Buka rincian untuk membaca keadaan request; jangan mengulang analisis otomatis.' },
  AWAITING_CONFIRMATION: { label: 'Perlu diperiksa', icon: 'reports', tone: 'ready', preparation: 'AWAITING_CONFIRMATION',
    description: 'Pelapor perlu membandingkan hasil AI dengan sumber lalu mengonfirmasi versi aktif. Ini berbeda dari pemeriksaan petugas.' },
  READY: { label: 'Siap dikirim', icon: 'check', tone: 'ready', preparation: 'READY',
    description: 'Versi aktif telah dikonfirmasi. Pengiriman masih memerlukan tindakan Kirim laporan pada halaman rincian.' },
  BLOCKED: { label: 'Perlu perbaikan', icon: 'alert', tone: 'ready', preparation: 'BLOCKED',
    description: 'Sumber atau hasil belum memenuhi syarat pengiriman. Buka rincian untuk membaca alasan dan langkah perbaikannya.' },
  FAILED: { label: 'Analisis gagal', icon: 'alert', tone: 'error', preparation: 'FAILED',
    description: 'Proses analisis gagal. Merah menunjukkan kegagalan operasi, bukan tingkat bahaya kejadian.' },
  SUBMITTED: { label: 'Sudah dikirim', icon: 'send', tone: 'sent', workflow: 'SUBMITTED',
    description: 'Versi resmi telah dikirim dan terkunci. Pengiriman belum berarti laporan selesai ditangani.' },
  ASSIGNED: { label: 'Ditugaskan', icon: 'user', tone: 'sent', workflow: 'ASSIGNED',
    description: 'Laporan telah ditugaskan kepada petugas sesuai keadaan yang tersimpan.' },
  IN_REVIEW: { label: 'Dalam pemeriksaan', icon: 'search', tone: 'review', workflow: 'IN_REVIEW',
    description: 'Petugas sedang memeriksa laporan.' },
  FOLLOW_UP: { label: 'Ditindaklanjuti', icon: 'wrench', tone: 'follow', workflow: 'FOLLOW_UP',
    description: 'Laporan berada pada tahap tindak lanjut.' },
  CLOSED: { label: 'Ditutup', icon: 'circle-check', tone: 'closed', workflow: 'CLOSED',
    description: 'Alur penanganan telah ditutup. Baca keputusan dan hasil penanganan pada rincian; status ini tidak menyatakan hasil AI pasti benar.' },
});
const unavailable = Object.freeze({ label: 'Status belum tersedia', icon: 'info', tone: 'draft' });
export const statusFilters = Object.freeze([
  { value: '', label: 'Semua Laporan' },
  ...Object.entries(reportStatuses).map(([value, status]) => ({ value, label: status.label })),
]);
export const legendStatuses = Object.freeze(['DRAFT', 'AWAITING_CONFIRMATION', 'SUBMITTED', 'IN_REVIEW', 'FOLLOW_UP', 'CLOSED']);

export function reportStatus(item) {
  if (!item) return unavailable;
  if (item.workflow_status !== 'NOT_SUBMITTED') return reportStatuses[item.workflow_status] || unavailable;
  return reportStatuses[item.preparation_status] || unavailable;
}

export function reportsPath(status = '', order = '-created_at', category = '', page = 1) {
  if (!statusFilters.some(item => item.value === status)) throw new Error('Filter status tidak dikenal.');
  if (!categoryFilters.some(item => item.value === category)) throw new Error('Filter kategori tidak dikenal.');
  if (!['created_at', '-created_at'].includes(order)) throw new Error('Urutan laporan tidak dikenal.');
  if (!Number.isSafeInteger(page) || page < 1) throw new Error('Halaman tidak dikenal.');
  const query = new URLSearchParams({ scope: 'owned', ordering: order, page_size: String(REPORT_PAGE_SIZE) });
  if (status) {
    const chosen = reportStatuses[status];
    query.set('workflow_status', chosen.workflow || 'NOT_SUBMITTED');
    if (chosen.preparation) query.set('preparation_status', chosen.preparation);
  }
  if (category) query.set('event_type', category);
  if (page > 1) query.set('page', String(page));
  return 'reports/?' + query;
}

export const incidentIcon = value => ({ FLOOD: 'waves', FIRE: 'flame', EARTHQUAKE: 'pulse', ACCIDENT: 'car', NON_EVENT: 'info' }[value] || 'file');
