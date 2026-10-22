# Checklist pemeriksaan SLR_10

Pembaruan dokumentasi: **23 Oktober 2026**. Status menggunakan arsip penyerahan SLR10 1.1.1, paket integrasi 0.2.0, keluaran terminal pelaksana dan konfirmasi manual PWA/tampilan. Setiap sumber bukti dipakai sesuai lingkupnya.

## Bukti penerimaan yang tersedia

| Bagian | Bukti tersedia | Status dan batas |
| --- | --- | --- |
| Vue/Router/Vite/Fetch/CSS | Source/lockfile, build historis dan aplikasi yang dijalankan pelaksana. | Frontend dapat dipakai sampai hasil analisis tersimpan; versi npm/build mengikuti arsip asalnya. |
| Akun/OTP/profil/logout | Halaman Vue, layanan SLR08 dan tes komponen/browser yang tercatat. | Bukti terdahulu dipertahankan; tidak diklaim semua kasus akun diulang pada 23 Oktober 2026. |
| Draft dan multimodal | API reporting, formulir asli, tes sambungan upload/bundle serta tujuh rute pada database aplikasi. | Tujuh kombinasi memiliki run berhasil; hubungan 10 run memenuhi pemeriksaan. |
| Evidence dan media privat | Decoder/tes SLR10 serta tes akses silang request, run, report dan media dalam suite integrasi. | Tes akses pemilik lulus pada PostgreSQL dengan model/provider pengganti. |
| Pemulihan sebelum bundle | GET evidence tanpa mutasi dan bukti tes/browser penyerahan SLR10. | Bukti lama dipakai sesuai bagian implementasi dan skenario yang diuji; bukan pengulangan manual baru. |
| Snapshot bundle | Pemilihan eksplisit, versi/hash/transaksi dan tes perubahan sumber melalui API. | Sumber baru dipertahankan dan kartu sumber lama tidak diaktifkan; konfirmasi manusia mengikuti SLR12. |
| NFR07 | Ringkasan, pagination, media on demand dan pemeriksaan terdahulu. | Rujuk hasil sesuai versi; log terbaru tidak diklaim sebagai inspeksi Network panel baru. |
| Analisis/pemulihan | 10 run aplikasi, pemeriksaan relasi serta 24 tes transaksi/integrasi lulus. | Tujuh rute, finalisasi, replay, respons hilang, konflik sumber, UNKNOWN dan fencing token memiliki bukti. |
| PWA | Manifest/ikon/SW dan tes cache/offline historis; konfirmasi manual terbaru. | Instalasi, muat ulang dan notifikasi offline berhasil menurut pelaksana. Inspeksi manual Cache Storage terbaru belum dilaporkan; batas cache privat tetap merujuk bukti implementasi/tes yang ada. |
| Responsif/awareness | Pemeriksaan viewport historis dan penilaian pelaksana terhadap frontend yang digunakan. | Pelaksana menilai tampilan tidak bermasalah. Perangkat/browser, ukuran viewport dan hasil keyboard/fokus terbaru tidak dirinci. |
| Database fondasi | Model/migration SLR08, termasuk history guards; eksekusi dua suite backend pada lingkungan pelaksana. | 24 tes lulus pada PostgreSQL; suite database memeriksa versi mayor 16. Database uji `test_silar_local`, Python 3.12.10. |
| Dokumentasi/commit | Hasil, checklist, penghubung integrasi, README dan bukti manual diselaraskan. | Reviewer/keputusan kelompok serta SHA/URL commit diisi dan dicocokkan pelaksana. |

## Status revisi 1.1.1 dan penerimaan integrasi

- [x] Durasi audio dihitung dari sampel decode; kasus tepat/melebihi 120 detik memiliki bukti tes revisi 1.1.1.
- [x] Launcher root diganti satu PANDUAN_RUNNING.md pada penyerahan 1.1.1.
- [x] Installer memiliki bukti perlindungan penghapusan berkas distribusi lama dengan hash dan backup.
- [x] Hasil transaksi/integrasi Windows/PostgreSQL dicatat dari keluaran pelaksana: 24 tes lulus.
- [x] Tujuh rute pada database aplikasi dan hasil pemeriksaan relasi 10 run dicatat.
- [x] Alur frontend sampai draft awal Incident Card tersimpan serta pemuatan ulang dicatat dari konfirmasi/screenshot pelaksana.
- [x] Instalasi PWA, muat ulang dan notifikasi offline dicatat sebagai keberhasilan yang dilaporkan pelaksana.
- [x] Penilaian pelaksana bahwa frontend yang digunakan tidak bermasalah dicatat dengan batas rincian perangkat/browser.
- [x] Dokumen SLR10 diselaraskan dengan bukti integrasi SLR11 dan catatan penerimaan manual.
- [ ] Review/keputusan kelompok dan Commit SHA/URL hasil pekerjaan tim dilengkapi oleh pelaksana setelah dibuat.

Checklist tersebut mencatat bukti dengan sumbernya; konfirmasi manual tidak diperluas menjadi pengujian semua browser/perangkat atau inspeksi cache privat baru. Penutupan card mengikuti kriteria penerimaan dan keputusan review kelompok berdasarkan bukti yang dirujuk.

## Rujukan bukti

- [Hasil verifikasi SLR10](HASIL_VERIFIKASI.md).
- [Penghubung SLR10–SLR11](INTEGRASI_SLR11.md).
- [Catatan penerimaan manual PWA dan tampilan](bukti-uji/penerimaan-manual-20261023.md).
- [Bukti pekerjaan dan waktu proses SLR11](../ai/slr11/BUKTI_PEKERJAAN_DAN_WAKTU_PROSES_SLR11.md).
- Log lengkap dan rekap terstruktur: `../ai/slr11/evidence/windows-pg16-20261023/`.

## Catatan Git

Periksa `git status` serta daftar berkas sebelum commit. .env, .venv, private_outbox, private_media, model_assets, node_modules dan backup lokal tidak disertakan. Pada ZIP penyerahan aplikasi SLR10, build dist disertakan untuk mencoba aplikasi dan diabaikan Git; source dan package-lock menjadi hasil utama frontend. Paket dokumentasi 23 Oktober 2026 berisi dokumen serta bukti penerimaan.

Sebelum commit, periksa berkas yang berubah, ditambahkan, dan dihapus melalui `git status --short` serta `git diff --name-status`. Pilih perubahan revisi ini, termasuk penghapusan launcher root, tanpa memasukkan pekerjaan rekan yang belum direview. Setelah commit/push benar-benar berhasil, catat SHA/URL pada card. Penyusunan ZIP tidak menjalankan operasi Git pada repository tim.

## Penutupan audit 1.1.0

Checklist rinci per R10-01 sampai R10-05 ada di REVISI_AUDIT_1.1.0.md. Hasil versi 1.0.0 berada dalam bukti-uji/historis-v1.0.0 dan tidak dipakai sebagai kelulusan baru. Setup dan halaman login Windows 1.0.0 yang diperlihatkan pemilik proyek belum menggantikan pengujian revisi 1.1.0.

Jika Node/npm belum terpasang, build bawaan tetap dapat dicoba dengan Python. Tes frontend dan pembangunan ulang pada laptop memerlukan Node sesuai engines package.json; jangan menandai langkah npm lulus bila belum dijalankan.

