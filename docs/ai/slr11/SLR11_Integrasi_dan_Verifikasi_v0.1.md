# SLR11 — Integrasi Pipeline AI dan Hasil Verifikasi

Versi implementasi 0.1.0 · 21 Oktober 2026

**Status: implementasi awal tersedia; SLR11 belum Done.** Uji komponen dan pemuatan model lokal telah dijalankan. Transaksi PostgreSQL 16, pemanggilan Gemini sebenarnya, serta alur bersama frontend/API input SLR10 belum terverifikasi.

Basis kode: `main` pada commit `8f805afcfe32b6f46b94043a55e196e23b824f7f`. Acuan: SILAR Technical Reference v0.3, terutama A4.22, A6 dan A7. Implementasi ini belum di-commit atau di-push.

## Hasil implementasi

Kode baru berada di `code/backend/ai_pipeline/`.

| Bagian | Berkas dan fungsi |
| --- | --- |
| Konfigurasi | `config.py`: lokasi aset, Whisper/Gemini dan deadline; AI yang belum siap tidak menghalangi pemuatan endpoint akun. |
| Input | `sources.py`, `audio.py`: tujuh kombinasi kanal asli, hash/ukuran/media privat, decoding gambar dan audio. Validator audio dapat digunakan SLR10 sebelum menerima unggahan. |
| Narasi | `narrative.py`, `clients.py`: Normalizer, Whisper lokal, Gemini melalui backend. Payload Gemini hanya teks/transkrip/gambar yang relevan. |
| Model | `runtime.py`: memakai kode SLR09 terbaru tanpa pelatihan ulang; memeriksa hash aset, label, konfigurasi dan versi dependensi. |
| Orkestrasi | `pipeline.py`: tujuh rute; revisi narasi hanya menjalankan SENA/NARA/Fusion. |
| Penyimpanan | `services.py`: reservasi kapasitas SLR08, penyimpanan tahap, finalisasi atomik, replay, pemeriksaan sumber dan fencing token. |
| API | `serializers.py`, `output.py`, `views.py`, `urls.py`: schema ketat dan proyeksi A6 tanpa kredensial, token eksekusi, PID atau path. |
| Pemulihan | `recovery.py` dan command `recover_ai_run`: UNKNOWN, bukti proses berhenti, penggantian token dan terminalisasi dengan audit. |
| Metadata | `runtime.safe_service_metadata()`: model/version dan keberadaan konfigurasi untuk SLR13. Bukan klaim kesehatan upstream; otorisasi monitoring tetap milik SLR13. |
| Pengujian | `tests/test_components.py`, `tests/test_database.py` dan empat fixture audio sintetis. |

Endpoint baru, relatif terhadap `/api/v1/`:

- `POST reports/{r}/analyses/`
- `GET reports/{r}/analysis-runs/{id}/`
- `GET requests/`
- `GET requests/{key}/`

Respons berhasil analisis adalah 201 Mutation, dengan `result.type` bernilai `Run`, objek Run dan `card_version_id`, setelah finalisasi berhasil commit. SLR10 memakai serializer hasil di `output.py` untuk melengkapi `ReportDetail`; draft kartu dibaca melalui detail laporan. Endpoint draft, unggahan, bundle dan frontend tetap dikerjakan pada SLR10.

Hasil tahap disimpan dengan pemeriksaan token/sumber dalam transaksi singkat. Inferensi berada di luar transaksi tersebut. Sumber berubah menghasilkan `INPUT_CHANGED` dan tidak mengaktifkan kartu lama. Hasil parsial tetap dapat ditelusuri. Fusion menghasilkan `AWAITING_CONFIRMATION`, atau `BLOCKED` untuk NON_EVENT; tidak membuat Human Verification atau melakukan submit resmi.

## Konfigurasi dan aset

| Komponen | Konfigurasi awal |
| --- | --- |
| SENA | v0.8.4, arsip `SILAR_SENA_context_v0.8.4_20261020.zip`. |
| NARA | reviewed pilot, arsip `SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip`. |
| Adapter/Fusion | Kode aktif SLR09, konfigurasi integrasi v0.9 dan lock kandidat v0.8.4; threshold operasional 0,95. |
| Whisper | `small` multilingual, CPU `int8`, faster-whisper 1.2.1. Aset `Systran/faster-whisper-small`, revisi `536b0662742c02347bc0e980a01041f333bce120`; hash berkas dicatat pada manifest lokal. |
| Gemini | `gemini-3.5-flash-lite`, SDK `google-genai` 2.32.0; key dari `GEMINI_API_KEY` di environment backend. |
| Audio | MP3, WAV PCM, WebM/Opus, M4A/MP4-AAC tanpa video. Satu audio per bundle, maksimal 10 MiB dan dua menit; audio internal mono 16 kHz, bukti asli dipertahankan. |
| Operasional | Dua thread CPU, kapasitas awal satu analisis, timeout Gemini 90.000 ms dan deadline antar-tahap 240 detik; angka operasional masih perlu pengukuran target. |

Dependensi gabungan ada di `code/backend/requirements-ai.txt`, yang menyertakan `requirements.txt` SLR08. Stack SLR09 dipertahankan: torch 2.11.0+cpu, transformers 4.57.1, tokenizers 0.22.1, safetensors 0.8.0, numpy 2.1.3. Pemeriksaan memakai Python 3.12.14/Linux; gabungan dependensi ini belum diuji pada Windows/Python 3.13.

Command `prepare_ai_models` memverifikasi arsip SENA/NARA sebelum mengekstrak whitelist berkas runtime. Opsi `--include-whisper --whisper-revision 536b0662742c02347bc0e980a01041f333bce120` menyiapkan revisi Whisper yang digunakan di sini. Request API tidak mengunduh model otomatis. Lokasi default: `code/backend/model_assets/`, yang dikecualikan dari Git.

`.env.example` menyediakan placeholder; key sebenarnya diisi lokal pada `.env` atau environment server. Rute teks saja/audio saja tidak memerlukan key Gemini. Rute gambar atau gabungan kanal memerlukan Gemini terkonfigurasi.

Cache model berlaku per proses. Kapasitas global satu analisis membatasi eksekusi, tetapi tidak menetapkan kebutuhan RAM beberapa proses backend. Jumlah proses, batas media, deadline dan timeout client/server/proxy harus diverifikasi sesuai A7.7. Deadline lokal diperiksa antar-tahap; tidak ada klaim penghentian paksa inferensi native pada detik tertentu.

## Verifikasi yang benar-benar dijalankan

| Pemeriksaan | Hasil | Bukti |
| --- | --- | --- |
| Uji komponen/kontrak | **30 lulus**, 0 gagal/error/skipped. | `evidence/component_tests.json` dan `.txt`. |
| Empat format audio | Semua berhasil didekode; ekstensi palsu, MIME tidak sesuai, berkas rusak dan durasi berlebih ditolak. | PyAV sebenarnya dengan fixture nada sintetis. |
| Tujuh rute/revisi narasi | Komponen dipilih sesuai kanal; revisi narasi tidak memanggil Whisper/Gemini. | Dependency pengganti pada uji orkestrasi. |
| Fusion SLR09 | Threshold tepat 0,95 tidak memicu low confidence; nilai di bawahnya memicu flag; NON_EVENT memblokir pengiriman. | Kode adapter/Fusion SLR09 sebenarnya pada input uji. |
| Batas Gemini | Payload dan output JSON diperiksa; konfigurasi SDK satu attempt. | Respons pengganti, **bukan panggilan Gemini nyata**. |
| Django/syntax/import | Lulus. | `evidence/django_check.txt`, compileall, pyflakes, `git diff --check`. |
| SENA/NARA lokal | Hash/dependensi cocok; inferensi dan Fusion pada tiga contoh sintetis baru. | `evidence/model_runtime_smoke.json`. |
| Whisper/jalur audio lokal | Model dimuat; audio tanpa ujaran ditolak. Ujaran sintetis diproses sampai Fusion. | Smoke yang sama; keterbatasan sampel dijelaskan di bawah. |
| PostgreSQL 16 | **Belum dijalankan**; 15 pengujian transaksi/API disiapkan. | `evidence/postgresql_verification.json`. |

Contoh aktual dari smoke SENA/NARA:

| Contoh | Kategori | Confidence mentah, dibulatkan | Contoh hasil NARA/Fusion |
| --- | --- | --- | --- |
| Banjir di Jalan Melati, Desa Sukamaju, pagi ini; tidak ada korban jiwa. | FLOOD | 0,99954 | Lokasi `Desa Sukamaju; Jalan Melati`, waktu `pagi ini`, korban `[]`, occurred_at `null`. |
| Mobil menabrak tiang di Jalan Mawar pukul 07.30; dua orang luka. | ACCIDENT | 0,99925 | Lokasi `Jalan Mawar`, korban `Dua orang mengalami luka`, objek mobil dan tiang. |
| Simulasi kebakaran di sekolah, bukan kebakaran sungguhan. | NON_EVENT | 0,99998 | event_type `null`; pengiriman diblokir. |

Contoh ini membuktikan pemuatan/eksekusi komponen pada lingkungan ini. Tidak dihitung sebagai akurasi, penerimaan mutu baru, atau pengulangan FINAL084. Training dan standar evaluasi SLR09 tidak diubah.

**Keterbatasan audio:** ujaran sintetis dibuat dengan FFmpeg/flite memakai suara berbahasa Inggris yang membacakan teks Indonesia. Transkrip aktual: `Benjir Munrendam Jalan Melati Tidak Eta Korban Jeewa`, kemudian SENA menghasilkan NON_EVENT. Jalur teknis berjalan, tetapi transkrip menyimpang. Sampel ini tidak mewakili mutu ujaran Indonesia alami; rekaman mikrofon/perangkat sasaran masih perlu diuji. Normalizer tidak menebak koreksi kata untuk menutupi kesalahan ASR. Flag uncertain mengikuti aturan SLR09 dan tidak otomatis mendeteksi kesalahan transkripsi. Audio sumber disertakan di `evidence/synthetic_speech_flite.wav`.

Angka RAM dari proses sandbox tidak diterima sebagai bukti kapasitas. Tidak ada klaim kebutuhan RAM minimum atau kelayakan VM target dari pemeriksaan ini.

## Verifikasi yang masih diperlukan

1. Jalankan 15 pengujian pada PostgreSQL 16 dengan migrasi dan trigger asli SLR08. Binary PostgreSQL 16.2 tersedia untuk percobaan, tetapi `initdb` menolak UID root dan sandbox tidak mengizinkan UID lain. SQLite tidak digunakan sebagai pengganti bukti PostgreSQL.
2. Uji Gemini sebenarnya dengan API key proyek, termasuk kuota, timeout serta narasi dari gambar/gabungan kanal.
3. Hubungkan layanan input dan frontend SLR10; buktikan login → unggah/rekam → bundle → analisis → pembacaan draft kartu.
4. Uji audio Indonesia alami, codec perangkat/browser sasaran serta CPU/RAM/deadline lingkungan demo.
5. Jalankan regresi backend SLR08 bersama integrasi, review kelompok, lalu catat commit hasil final.

Suite PostgreSQL mencakup finalisasi/rollback, replay tanpa inferensi ulang, perubahan izin, capacity lock lintas koneksi, sumber berubah, UNKNOWN, pembacaan tanpa mutasi dan fencing token. Pengujian tersedia di `tests/test_database.py`; belum dinyatakan lulus. Pemeriksaan komponen tidak menggantikan suite tersebut.

## Pemulihan teknis A7.5

Command hanya untuk pengelola backend yang memiliki akses konsol; tidak ada endpoint retry Admin.

1. `python manage.py recover_ai_run RUN_ID --inspect` membaca identitas proses dan execution_token internal tanpa mutasi. Cocokkan run, host, PID dan waktu mulai dengan proses/log.
2. Jika hasil belum pasti, `--mark-unknown --expected-token TOKEN` menandai UNKNOWN dengan audit; slot tetap ditahan.
3. Hentikan dan buktikan proses API lama berhenti pada host asal, lalu gunakan `--abort-stopped --expected-token TOKEN`. Command menolak proses hidup, host berbeda atau keadaan yang tidak dapat dibuktikan; bukti sah menyebabkan token diganti dan run diterminalkan FAILED RECOVERY_ABORTED.

Timeout/hilangnya lock saja bukan bukti penghentian. Setelah terminalisasi sah, Reporter membaca keadaan terbaru dan melakukan retry eksplisit dengan key baru. Sumber baru dipertahankan jika sumber run lama sudah berubah.

## Berkas bersama dan penyerahan

`SLR11_Perubahan_Berkas_Bersama.patch` memperlihatkan tambahan pada `.env.example`, `config/settings.py` dan `config/urls.py` untuk digabung dengan pendaftaran input SLR10. Modul URL dan dependensi AI disediakan terpisah; fondasi model/izin/audit SLR08 serta kode/evaluasi SLR09 digunakan kembali.

Paket berisi kode baru, tiga berkas bersama versi basis commit di atas, patch perubahannya, laporan ini dan bukti verifikasi. Patch digunakan untuk menyatukan tambahan tersebut dengan pekerjaan SLR10. Bobot model, `.env`, virtual environment, media privat dan cache tidak termasuk paket.
