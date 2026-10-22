# Penghubung SLR_10 dan SLR_11

SLR_10 menyediakan aplikasi Vue dan sumber input tersimpan. SLR_11 menyediakan pipeline sinkron, narasi, Whisper/Normalizer/Gemini, SENA, NARA, Fusion, ledger/run serta finalisasi hasil. Tidak ada pipeline atau aset model baru yang dibuat dalam paket SLR_10 ini.

## Titik integrasi

SLR_11 membaca `core.Report`, `EvidenceItem`, `EvidenceBundle`, dan `EvidenceBundleItem`. Urutan sumber berasal dari Bundle.items.position. Bukti teks asli tersedia pada EvidenceItem.text_content; audio/gambar dibaca dari private storage dengan file_key hanya di backend. Client tidak menentukan kategori model atau mengirim bukti langsung ke Gemini.

Frontend mengirim:

```json
{
  "mode": "EVIDENCE",
  "bundle_id": "UUID bundle aktif dari respons backend",
  "input_revision": 2,
  "expected_revision": 4
}
```

UUID di atas penanda dokumentasi; aplikasi mengirim nilai nyata. Request ditujukan ke `POST /api/v1/reports/{r}/analyses/` dengan Idempotency-Key baru dari tindakan pengguna. SLR_11 melakukan reservasi/finalisasi dan menyimpan seluruh hasil sebelum respons sukses. Tidak ada auto retry POST ketika koneksi putus.

Frontend membaca kembali `GET reports/{r}/` dan memakai `current_card`, `active_narrative`, `latest_run.sena/nara`, status dan revision. Helper `reporting.serializers.run_data` serta `detail_data` menyediakan schema A6.5 dari model core yang sudah ada. Bila SLR_11 menyediakan implementasi ReportDetail sendiri, gunakan satu penyajian yang konsisten; jangan mendaftarkan dua route detail yang saling menutupi.

Pemulihan analisis menggunakan `GET requests/?report_id=...`, `GET requests/{key}/` dan `GET reports/{r}/analysis-runs/{id}/` milik SLR_11. Tombol Periksa status membaca keadaan; tidak melanjutkan inferensi. RUNNING dan UNKNOWN tetap menahan analisis baru.

## Pemasangan route tanpa menimpa

`config/urls.py` SLR_10 menambahkan include `reporting.urls`. Modul ini hanya memiliki endpoint daftar/detail Report, evidence, media dan bundle. Tidak ada stub route analyses yang menutupi implementasi SLR_11. Rekan dapat menambahkan include URL pipeline pada awalan `/api/v1/` yang sama. Semua route tetap memakai trailing slash.

Nama `ai_pipeline/` mengikuti rencana MEET_06; sesuaikan include dengan nama modul aktual yang dibuat pelaksana SLR_11. Dependency AI ditambahkan ke berkas requirements terpisah agar fondasi akun dan decoder input tetap dapat dijalankan tanpa memuat model.

## Kriteria uji bersama

1. Login nyata, buat Report, upload media dan pilih bundle melalui aplikasi.
2. Jalankan tujuh kombinasi kanal. Teks/audio tunggal tidak mengirim data ke Gemini; lima kombinasi terkait memberi informasi pemrosesan eksternal sebelum tindakan.
3. Pastikan narasi, hasil SENA/NARA, versi model, Fusion dan kartu sudah commit sebelum respons sukses.
4. Periksa NON_EVENT dan uncertain dari hasil aktual. Aplikasi tidak menghitung confidence atau membuat field kejadian yang hilang.
5. Uji respons hilang, perubahan sumber saat run, konflik revision, replay, RUNNING/UNKNOWN serta pembacaan hasil setelah reload sesuai A7.4/A7.5.
6. Catat lingkungan, model/adapter versi, input uji, status, hasil, commit serta keterbatasan. Fixture unit dan SQLite komponen tidak menjadi bukti inferensi model nyata atau constraint PostgreSQL.

Koreksi narasi/field, Human Verification, konfirmasi dan submit resmi tetap berada pada SLR_12. Pengelolaan Operator/Admin dan Portal Publik dilengkapi pada SLR_13/SLR_14. Tampilan ruang akun non-Reporter di SLR_10 tidak mengklaim dashboard tersebut sudah selesai.

## Penyelarasan audit 1.1.0 (riwayat)

- Profil audio: MP3, WAV PCM, WebM/Opus, M4A/MP4-AAC tanpa video atau cover gambar; OGG/ALAC/Vorbis ditolak. Bukti tidak diubah menjadi format lain oleh SLR_10. Resampling mono 16 kHz untuk Whisper tetap SLR_11.
- Pillow 13.0.0 merupakan pin dasar. Requirements AI yang masih memakai pin lain dihentikan oleh preflight agar tidak terjadi downgrade diam-diam. Setup menggunakan resolver gabungan bila requirements-ai.txt tersedia.
- Pembacaan normalization_warnings tidak mengubah uncertain atau hasil model. UI mencocokkan bundle, narrative, sena_result, nara_result, dan analysis_run sebelum menampilkan confidence/peringatan dari run terbaru. Ketika run terbaru gagal atau belum cocok, kartu tersimpan diberi keterangan dan metadata run baru tidak dicampurkan.
- Saat penyusunan versi 1.1.0 belum ada salinan kode/dependensi lengkap SLR_11 pada lingkungan penyusun. Pemeriksaan loader load_sources, resolver lengkap AI, tujuh rute nyata dan PostgreSQL 16 tetap menjadi pengujian gabungan di repository tim; hasil audit historis tidak dihitung ulang sebagai bukti versi 1.1.0.

## Penyelarasan 1.1.1

Validator SLR10 menghitung panjang isi audio hasil decode menjadi PCM mono 16 kHz, sama dengan satuan batas decoder SLR11. Padding metadata pada MP3/WebM tepat 120 detik tidak lagi menyebabkan penolakan sebelum decode. Batas tetap 120 detik dan bukti asli tidak ditulis ulang.

Panduan menjalankan kedua layanan ada pada `../../PANDUAN_RUNNING.md`. Tambahan konfigurasi kedua modul tetap digabung secara terarah; installer tidak mengganti source atau requirements AI. Hasil pemeriksaan penghubung yang benar-benar dijalankan dirangkum pada `HASIL_VERIFIKASI.md`; pengujian loader dibedakan dari inferensi model/API nyata.
