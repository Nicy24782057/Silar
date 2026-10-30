# SLR14 — keputusan yang telah disepakati

Acuan utama: Technical Reference SILAR v0.3 (termasuk 9.1.1), paket desain
`SILAR_Seluruh_Role_Palet_Terang (2)(1).zip`, dan
`SILAR_Login_Visual_Biru(1).svg`. Persetujuan pengguna diberikan setelah
peninjauan desain dan revisi pratinjau akun pada 29 Oktober 2026.

## Kontrak dan informasi publik

Kontrak API dipertahankan. PublicReport hanya berisi id, event_type, summary,
general_location, time_text, occurred_at, general_impact, handling_update,
dan published_at. Kandidat privat tidak boleh menjadi sumber Portal Publik.

| Label pada desain | Label implementasi | Sumber |
| --- | --- | --- |
| Lokasi | Lokasi | general_location |
| Waktu yang disebut | Waktu yang disebut | time_text |
| Waktu pasti | Waktu pasti | occurred_at |
| Dampak | Dampak umum | general_impact |
| Objek terdampak | Ringkasan kejadian | summary |
| Pihak terlibat | Perkembangan penanganan | handling_update |
| Informasi korban | Waktu publikasi | published_at |
| Versi 2 | Informasi publik | Teks tetap |

Nilai opsional yang tidak tersedia tetap ditandai demikian. Waktu publikasi
tidak digunakan untuk mengisi waktu kejadian. Identitas Reporter, bukti privat,
hasil AI mentah, alasan internal, dan ID versi internal tidak menjadi data publik.

## Penempatan publikasi

Panel publikasi berada di Detail Laporan Operator, tab Keputusan, di bawah
bagian arah keputusan. Tujuh tab tetap dipertahankan. Form informasi publik,
pratinjau, pembentukan kandidat, persetujuan, penerbitan, dan pembatalan merupakan
tindakan yang berbeda. Isi versi yang sudah disimpan tidak ditimpa; perbaikan
memakai kandidat pengganti. Versi terbit lama tetap tersedia sampai pengganti terbit.

## Identitas dan responsivitas

Warna, logo, pola, ilustrasi, tipografi dan kedua tema mengikuti referensi.
Panel identitas akun menggunakan sumber SVG asli, tanpa potongan logo yang
menambahkan latar. Judul dan label formulir memakai warna teks eksplisit.

- Desktop dan tablet: panel identitas dan panel formulir.
- Ponsel: hanya panel formulir kanan, tanpa banner identitas tambahan.
- Registrasi, verifikasi email, aktivasi Operator, lupa/reset kata sandi
  mengikuti kerangka Login dan alur API yang telah ada.
- Pendaftaran publik hanya untuk Reporter; Operator dibuat oleh Admin.
- Portal Publik: 5 kolom desktop, 2 tablet, 1 ponsel; 10 kartu per halaman.
- Pagination di bawah daftar: Sebelumnya, halaman aktif, Selanjutnya.
- Pencarian/perubahan filter kembali ke halaman pertama. Urutan mengikuti backend.
- Pada layar kecil, sidebar aplikasi dapat dibuka dan tabel dapat digeser mendatar.

## Batas pekerjaan

Penyeragaman antarmuka mencakup Reporter, Operator, Admin, halaman bersama,
akun, landing page dan Portal Publik. Angka/nama/ID pada SVG adalah contoh,
bukan data produksi. Angka ringkasan harus mencakup seluruh lingkup yang sah,
bukan hanya halaman daftar yang sedang terlihat. Tidak ada penyimpanan data
laporan, bukti atau token secara offline. Preferensi tema tetap diperbolehkan.

Perubahan dikerjakan pada branch terpisah dari main. Dokumen hasil pengujian
harus membedakan pemeriksaan komponen dan transaksi PostgreSQL 16.

## Revisi yang disetujui 30 Oktober 2026

Navigasi Portal Publik mengikuti landing page: logo asli, Beranda, Alur
pelaporan, SENA & NARA, Portal Publik aktif, mode warna, Masuk dan Buat akun.
Ilustrasi harus utuh di dalam banner dan tidak menimpa teks. Empat tahap
halaman pelaporan dan keadaan memuat/kosong/gagal mengikuti SVG dalam ZIP
referensi. Persetujuan ini memperjelas penyeragaman yang sudah termasuk
lingkup SLR14; kontrak API dan pemetaan isi publik pilihan B dipertahankan.

## Audit lanjutan 30 Oktober 2026

Setelah pengguna menyetujui kelanjutan audit, penghapusan draft diterapkan secara
logis: hanya pemilik Reporter aktif/terverifikasi, belum dikirim, tanpa menghapus
bukti/versi/audit. Migration 0005 dan tambahan DELETE didokumentasikan di
[API_HAPUS_DRAFT.md](API_HAPUS_DRAFT.md). Keputusan B publik dan syarat/izin
publikasi sebelumnya tetap berlaku. Tidak ada push/deploy pada tahap ini.

## Permintaan lanjutan: alur dan umpan balik

Pengguna meminta transisi login lebih halus, loading analisis dengan persentase,
urutan Lanjut/Kembali, dan halaman keberhasilan pengiriman. Implementasi memakai
persentase tahapan tersimpan dari API yang sudah ada dan memverifikasi pengiriman
sebelum memperlihatkan halaman berhasil. Rinciannya ada di
[ALUR_DAN_PROGRES_20261030.md](ALUR_DAN_PROGRES_20261030.md).

## Umpan balik lanjutan: notifikasi dan pembukaan hasil

Pengguna meminta notifikasi Admin dirapikan dan tampilan tahap draft kembali
seperti sebelumnya, dengan animasi analisis dipertahankan. Sesudah analisis dan
pembacaan hasil berhasil, Periksa hasil kini terbuka otomatis. Permintaan ini
menggantikan kewajiban menekan Lanjut setelah analisis pada revisi alur awal.
Penanda tetap nonklik, serta konfirmasi dan submit tetap eksplisit. Rincian:
[REVISI_NOTIFIKASI_DAN_HASIL_20261030.md](REVISI_NOTIFIKASI_DAN_HASIL_20261030.md).

## Umpan balik lanjutan: alur Operator

Pengguna meminta keberhasilan review lebih jelas, pratinjau publikasi langsung
tersedia, serta perpindahan proses lebih halus. Revisi menyatukan persiapan
keputusan/versi/persetujuan di balik Konfirmasi isi publikasi, dengan publish
tetap sebagai tombol terpisah. Semua operasi memakai API dan audit yang sudah
ada. Rincian dan batasnya: [ALUR_OPERATOR_20261030.md](ALUR_OPERATOR_20261030.md).
