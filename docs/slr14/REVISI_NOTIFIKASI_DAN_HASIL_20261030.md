# Revisi notifikasi, tampilan tahap draft, dan hasil analisis otomatis

Revisi berdasarkan umpan balik pengguna pada 30 Oktober 2026. Paket ini kumulatif
terhadap SLR13 dan mencakup paket alur sebelumnya. Hanya enam berkas frontend
berubah untuk revisi ini; tidak ada perubahan API, backend, migration, atau
dependensi baru pada revisi lanjutan ini.

## Hasil perubahan

1. **Notifikasi Admin.** Ikon lonceng, judul dan keterangan kosong disejajarkan di
   kiri. Aturan `.empty` umum sebelumnya menambahkan padding kedua dan meratakan
   teks ke tengah pada komponen FetchState. Reset di komponen mencegah benturan
   ini, termasuk pada halaman lain yang memakai keadaan kosong yang sama.
   Pembacaan lambat/gagal tetap dibedakan dari daftar kosong. Filter dan
   penandaan dibaca mempertahankan perilaku API yang sudah ada.
2. **Penanda tahap draft.** Tampilan kembali berupa tiga kartu berbingkai dan
   sudut membulat; tahap aktif memakai gradasi biru pada mode terang, warna gelap
   sesuai acuan, teks putih dan nomor tahap. Label/caption dan indikator kunci
   mengikuti acuan Reporter 02. Gaya pada `report-compose.css` kini diterapkan
   kepada elemen indikator nonklik. Varian garis bawah dari revisi alur dihapus.
   Penanda tidak dapat digunakan untuk meloncat tahap.
3. **Hasil otomatis setelah analisis.** Animasi dan persentase tahapan tetap.
   Sesudah POST selesai, laporan dibaca lagi. Run, bundle, revisi input, narasi
   serta Incident Card harus cocok sebelum hasil dinyatakan siap. Setelah itu
   otomatis terbuka **Periksa hasil**, tanpa menekan Lanjut. Fokus dan scroll
   mengikuti judul tahap. Respons gagal atau pembacaan yang belum pasti tidak
   memindahkan pengguna ke hasil lama dan tidak mengulangi POST otomatis.

Dari Periksa hasil, tombol **Lanjut ke konfirmasi** tetap diperlukan. Koreksi
yang belum disimpan menahan perpindahan. Konfirmasi versi dan pengiriman tetap
dua tindakan terpisah. Halaman laporan terkirim tetap ditampilkan sesudah
keberhasilan submit dibuktikan dari API. Tombol Lanjut dari bukti masih tersedia
untuk membuka kembali hasil tersimpan ketika pengguna sengaja kembali ke bukti.

## Verifikasi revisi ini

| Pemeriksaan | Hasil | Bukti |
| --- | --- | --- |
| Unit frontend | 103 lulus | `bukti/frontend-unit.txt` |
| Build produksi | Lulus | `bukti/frontend-build.txt` |
| Notifikasi Admin | 24 kombinasi kosong/berisi, dua tema × enam lebar | `bukti/notifikasi-dan-hasil.txt` |
| Penanda draft | 12 kombinasi, dua tema × enam lebar | `bukti/notifikasi-dan-hasil.txt` |
| Analisis otomatis | Lulus | Progres bertahap, pembacaan ditahan sebelum hasil dibuka, satu POST, gagal tetap di bukti |
| Konfirmasi dan submit | Lulus melalui API lokal | Urutan tombol, koreksi belum disimpan, receipt, refresh, URL draft belum terkirim |
| Regresi Reporter/portal | 60 kombinasi dan alur API lulus | `bukti/browser-reporter-notifikasi.txt`; teks/WAV/PNG, koreksi versi, konfirmasi dan submit |
| PWA produksi | Lulus, 60 aset UI | `bukti/pwa-notifikasi.txt`; shell offline, tanpa cache API/media/laporan/kredensial |

Enam lebar: 1440, 1100, 820, 640, 390 dan 320 px. Pemeriksaan tidak menemukan
error runtime atau luapan dokumen pada kasus yang diperiksa. Notifikasi berisi
mencakup pesan panjang, status dibaca/belum dibaca dan satu PATCH nyata untuk
menandai dibaca. Retry pembacaan memakai GET.

Pengujian progres memakai respons API terkontrol, bukan inferensi model baru.
API lokal lainnya memakai database QA terpisah dengan pemeriksaan integritas.
Hasil backend/native PostgreSQL dari paket sebelumnya tidak diuji ulang karena
backend tidak berubah. Batas sebelumnya tetap pada [HASIL_VERIFIKASI.md](HASIL_VERIFIKASI.md).

Bukti visual terbaru: `bukti/notifikasi-admin-*`, `bukti/draft-tahapan-*`, dan
`bukti/hasil-otomatis-gelap.png`. Bukti berawalan `alur-` berasal dari paket alur
sebelumnya; gunakan bukti revisi ini untuk tampilan penanda tahap terkini.

## Memasang

Gabungkan `code/` dan `docs/slr14/` menurut path ke proyek yang menjalankan SLR13.
Jangan mengganti seluruh folder proyek. Petunjuk ada di `MULAI_DI_SINI.txt` dan
[README.md](README.md). Jika migration 0005 dari paket sebelumnya telah berjalan,
revisi ini tidak memerlukan migration tambahan. Gunakan build/PWA terbaru.
