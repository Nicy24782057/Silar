# Hasil uji penerimaan FINAL083 SLR_09 v0.8.3

**Status mutu: belum lulus. Status pekerjaan: In Review.** Eksekusi pengujian selesai pada 20 Oktober 2026. Enam dari sembilan pemeriksaan terpenuhi. Tiga yang belum terpenuhi ialah recall NON_EVENT, isi berlebih pada field kosong, dan kontras simulasi/latihan dengan kejadian nyata.

## Acuan dan koreksi yang disetujui

Reviewer pada Excel: Bintang. Sebanyak 50 narasi dan 685 token sudah APPROVED, dengan 10 narasi tiap kelas dan seluruh 14 role non-O. Pesan pengguna “oke setuju dan lanjut” pada 20 Oktober 2026 pukul 21:10:35 WIB mengesahkan dua koreksi yang sebelumnya diusulkan:

- Token!D531, peserta pada FINAL083-NON_EVENT-01: O menjadi OFFICER-ARG.
- Token!D574, penyebutan gempa kedua pada FINAL083-NON_EVENT-03: O menjadi FALSE-EVENT.

Perbandingan menyeluruh memastikan hanya dua nilai label itu berubah. ID, teks, kategori, field, keputusan review, rumus, freeze panes, tabel dan dropdown dipertahankan. Berkas masukan asli tersimpan sebagai bukti. SHA256 Excel final: `2e9cfb9ee4b45ded92baa190d0348b55464fdc3c4b570da2436ef314a2adf352`.

## Hasil terukur

| Pemeriksaan | Hasil | Target | Status |
| --- | ---: | ---: | --- |
| SENA macro F1 | 95.87% | ≥85% | Lulus |
| Recall NON_EVENT | 80.00% | ≥90% | Belum lulus |
| Recall minimum empat kelas kejadian | 100.00% | ≥80% | Lulus |
| NARA macro F1 seluruh 14 non-O | 88.51% | ≥75% | Lulus |
| NARA exact span F1 | 82.83% | ≥60% | Lulus |
| Field nonkosong tepat | 84.04% | ≥80% | Lulus |
| Isi berlebih pada field kosong | 6.79% | ≤5% | Belum lulus |
| Kontrak adapter dan Fusion | 0 kesalahan | 0 kesalahan | Lulus |
| Kontras simulasi/latihan dan kejadian nyata | 2 salah | Semua benar | Belum lulus |

SENA benar pada 48/50 narasi (96%). Empat kelas kejadian masing-masing memiliki recall 100%; NON_EVENT benar 8/10. Field nonkosong tepat adalah 158/188, sedangkan isi berlebih terjadi pada 11/162 field acuan kosong. Metrik field tidak menggunakan kecocokan kosong untuk menaikkan skor nonkosong.

## Dua kesalahan kategori

| ID | Acuan | Prediksi SENA | Confidence | Ditandai di bawah cutoff |
| --- | --- | --- | ---: | --- |
| FINAL083-NON_EVENT-03 | NON_EVENT | EARTHQUAKE | 66.52% | Ya |
| FINAL083-NON_EVENT-04 | NON_EVENT | FLOOD | 72.96% | Ya |

Narasi pertama menyatakan getaran buatan dalam peragaan serta bukan gempa sungguhan. Narasi kedua menyatakan banjir dalam latihan yang ditiru dengan kolam kecil, sementara permukiman tetap kering. Keduanya beracuan NON_EVENT. Prediksi SENA masih mengikuti kata kejadian pada dua konteks tersebut.

Cutoff tetap 0,95. Kedua kesalahan mempunyai flag LOW_CLASSIFICATION_CONFIDENCE. Total lima narasi ditandai di bawah cutoff, termasuk kedua kesalahan. Tidak terdapat kesalahan kategori pada confidence ≥0,95 dalam pilot ini. Temuan pada 50 narasi tersebut tidak membuktikan kalibrasi probabilitas atau jaminan akurasi 95% di lapangan. Kategori tetap berasal dari SENA dan tidak diganti oleh FALSE-EVENT NARA.

## Isi berlebih pada acuan kosong

Semua baris di bawah memiliki acuan kosong pada field terkait.

| ID | Field | Isi prediksi |
| --- | --- | --- |
| FINAL083-FLOOD-05 | impacts | ["mengonfirmasi"] |
| FINAL083-FLOOD-07 | impacts | ["mengakibatkan seorang warga terluka"] |
| FINAL083-EARTHQUAKE-08 | impacts | ["menimbulkan satu korban meninggal"] |
| FINAL083-FIRE-05 | impacts | ["Pemeriksaan petugas desa"] |
| FINAL083-FIRE-07 | impacts | ["mengakibatkan satu pemilik rumah terluka"] |
| FINAL083-FIRE-09 | involved_parties | ["semua orang"] |
| FINAL083-NON_EVENT-01 | affected_objects | ["kendaraan"] |
| FINAL083-NON_EVENT-04 | affected_objects | ["permukiman"] |
| FINAL083-NON_EVENT-05 | impacts | ["sampai", "belum ada kejadian"] |
| FINAL083-NON_EVENT-06 | impacts | ["membantah", "pemeriksaan tidak menemukan"] |
| FINAL083-NON_EVENT-09 | location_text | "negeri rekaan" |

Pola yang perlu diperbaiki mencakup keterangan pelaporan yang terbaca sebagai dampak, pengulangan keterangan korban ke field dampak, objek pada simulasi, dan lokasi rekaan. Daftar lengkap 41 perbedaan field serta kesalahan token NARA tersedia dalam evaluation.json. Acuan manusia tidak disesuaikan dengan keluaran model.

## Bukti dan cakupan

Notebook 28 benar-benar dieksekusi lewat CPython cell executor. Salinan `_executed` menyimpan stream dan metadata eksekusi, tanpa klaim kernel Jupyter asli. Acuan divalidasi dan dibekukan, lalu 21 berkas sumber terikat disalin sebelum pemuatan model. Kedua arsip dimuat setelah pemeriksaan SHA256. Inferensi SENA dan NARA berjalan pada seluruh 50 narasi tanpa pemotongan; semua 685 token diproses. Penghitungan ulang dari prediksi tersimpan memberikan hasil yang identik.

Bobot SENA tetap SILAR_SENA_context_v0.8.3_20261020.zip dan NARA tetap SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip. Tidak ada pelatihan atau perubahan implementasi kandidat pada tahap ini. Pengujian memakai CPU lingkungan representatif, bukan bukti target VM atau backend submission.

Pilot terdiri dari 50 narasi sintetis buatan asisten yang diperiksa manusia. Tidak ada exact overlap ternormalisasi terhadap sumber tersedia. Keanggotaan seluruh sumber pada training awal belum dapat dibuktikan dan generalisasi populasi belum ditetapkan.

## Kelanjutan

Prioritas berikutnya ialah dua pola false event SENA dan presisi field NARA. Hasil penerimaan pertama, sumber review dan label manusia tetap dipertahankan. Jika kesalahan FINAL083 dipakai mengubah model atau kode, set ini harus dipensiunkan menjadi development/regresi dan uji penerimaan berikutnya memerlukan acuan manusia baru. Pada checkpoint ini, FINAL083 belum dipakai melatih atau memilih ulang kandidat.

Persetujuan mutu, Done dan deployment tetap false. Hasil lengkap tersedia dalam SLR09_Bukti_Penerimaan_FINAL083_v0.8.3.zip.
