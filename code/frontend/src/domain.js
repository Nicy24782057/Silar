export const LIMITS = Object.freeze({text: 5000, image: 5 * 1024 ** 2, audio: 10 * 1024 ** 2, bundle: 25 * 1024 ** 2});
export const labels = {DRAFT:'Draft', PROCESSING:'Sedang dianalisis', AWAITING_CONFIRMATION:'Perlu diperiksa', READY:'Sudah dikonfirmasi',
  BLOCKED:'Pengiriman ditahan', FAILED:'Proses gagal', NOT_SUBMITTED:'Belum dikirim', SUBMITTED:'Menunggu Operator', ASSIGNED:'Ditugaskan',
  IN_REVIEW:'Dalam pemeriksaan', FOLLOW_UP:'Tindak lanjut', CLOSED:'Ditutup', NOT_REVIEWED:'Belum diperiksa', VALID:'Valid', INVALID:'Tidak valid',
  INCONCLUSIVE:'Belum dapat dipastikan', NOT_DECIDED:'Belum diputuskan', INTERNAL:'Internal', PENDING_APPROVAL:'Persiapan publikasi',
  APPROVED:'Disetujui', PUBLISHED:'Terbit', RUNNING:'Masih diproses', UNKNOWN:'Hasil belum pasti', SUCCEEDED:'Hasil tersimpan',
  FLOOD:'Banjir', EARTHQUAKE:'Gempa bumi', FIRE:'Kebakaran', ACCIDENT:'Kecelakaan', NON_EVENT:'Bukan laporan kejadian'};
export const label = value => labels[value] || value || 'Belum tersedia';
export const textLength = value => Array.from(value).length;
export function validateText(value) {
  if (!value.trim()) return 'Tulis keterangan kejadian terlebih dahulu.';
  if (textLength(value) > LIMITS.text) return 'Teks maksimal 5.000 karakter.';
  return '';
}
export function validateFile(file, kind) {
  const extensions = kind === 'IMAGE' ? /\.(png|jpe?g)$/i : /\.(wav|mp3|m4a|mp4|webm)$/i;
  if (!file || !file.size) return 'Pilih berkas yang tidak kosong.';
  if (!extensions.test(file.name)) return kind === 'IMAGE' ? 'Gunakan PNG atau JPEG.' : 'Gunakan WAV PCM, MP3, WebM/Opus, atau M4A/MP4 dengan AAC tanpa video.';
  if (file.size > LIMITS[kind.toLowerCase()]) return kind === 'IMAGE' ? 'Gambar maksimal 5 MiB.' : 'Audio maksimal 10 MiB.';
  return '';
}
export function validateBundle(items) {
  if (!items.length) return 'Pilih sedikitnya satu bukti tersimpan.';
  const count = type => items.filter(x => x.type === type).length;
  if (count('TEXT') > 1 || count('AUDIO') > 1 || count('IMAGE') > 3) return 'Pilih maksimal satu teks, satu audio, dan tiga gambar.';
  if (items.reduce((sum, item) => sum + item.byte_size, 0) > LIMITS.bundle) return 'Total bukti maksimal 25 MiB.';
  return '';
}
export function usesGemini(items) {
  const kinds = new Set(items.map(x => x.type));
  return kinds.has('IMAGE') || (kinds.has('TEXT') && kinds.has('AUDIO'));
}
export function paginationPath(value) {
  const url = new URL(value, 'http://localhost');
  if (!url.pathname.startsWith('/api/v1/')) throw new Error('Alamat halaman API tidak sah.');
  return url.pathname.slice('/api/v1/'.length) + url.search;
}
export const size = bytes => bytes < 1024 ? bytes + ' B' : bytes < 1024 ** 2 ? (bytes / 1024).toFixed(1) + ' KiB' : (bytes / 1024 ** 2).toFixed(1) + ' MiB';
export const date = value => value ? new Intl.DateTimeFormat('id-ID', {dateStyle:'medium', timeStyle:'short'}).format(new Date(value)) : 'Belum tersedia';
