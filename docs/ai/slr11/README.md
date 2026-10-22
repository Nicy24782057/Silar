# Integrasi SLR10 dan SLR11

Versi integrasi 0.2.0, 22 Oktober 2026. Basis repository: `main` pada `6b3a6ce7b9108bbf7fd175814f56d6ffb75f3f88`. Sumber AI: `SLR11_Implementasi_Awal_v0.1_20261021.zip`. Implementasi pipeline tetap memakai identitas versi 0.1.0; 0.2.0 menandai penyerahan integrasi ini, bukan pelatihan atau versi model baru.

Source sudah menggabungkan akun, input, bundle, analisis sinkron dan pembacaan hasil tersimpan. Penerimaan PostgreSQL, perangkat sasaran dan inferensi nyata pada source gabungan dicatat setelah pengujian tim; card SLR11 belum dinyatakan Done dari tes komponen.

## Acuan

- PRD SILAR v0.5: `docs/product/SILAR_PRD.docx`.
- Acuan Teknis v0.3: A4.22, A6.2/A6.4–A6.6 dan A7.3–A7.8 pada `docs/architecture/SILAR_Technical_Reference.docx`.
- Keputusan MEET_05 dan card SLR11: `models/slr09/sources/governance/MEET.md` serta `SILAR_Card_SLR07-16_Final.md`.
- Pemetaan fitur: `docs/planning/SILAR_Pemetaan_Fitur_Final.md`.

## Batas integrasi

| Kebutuhan | Implementasi | Bukti pada source gabungan |
| --- | --- | --- |
| FR05 | Tujuh kanal asli: T, A, I, TA, TI, AI, TAI; `sources.py`, `audio.py`, `pipeline.py`. | Sembilan tes sambungan mencakup tujuh rute dari API upload/bundle hingga kartu persisten; client model/provider merupakan double eksplisit. |
| FR06 | Normalizer untuk T/A tunggal; Gemini untuk gambar/kombinasi; narasi tersimpan dan bertaut ke sumber. | Referensi narasi/run serta payload provider diuji; tidak ada klaim mutu narasi dari provider nyata pada pengujian integrasi ini. |
| FR07/FR08 | Runtime SENA/NARA aktif SLR09, versi hasil, raw/normalized output dan peringatan. | Proyeksi hasil SLR10 sama dengan pembacaan run SLR11 pada graph persisten; model aktif tidak dilatih atau diubah. |
| FR09 | Fusion dan draft awal Incident Card; NON_EVENT/BLOCKED serta uncertain. | Kartu tetap NOT_SUBMITTED dan tidak membuat HumanVerification. |
| FR10/NFR10 | Request sinkron, reservasi, hasil parsial, finalisasi, ledger, replay, RUNNING/UNKNOWN dan recovery teknis. | Tes komponen serta pembacaan request/run; 15 tes transaksi PostgreSQL tersedia untuk lingkungan tim. |
| NFR03 | Allowlist data Gemini; audio asli dan kredensial tidak dikirim. | Tes client memeriksa payload dengan respons pengganti; key aktual tetap lokal. |
| NFR07 | Detail/media on demand, pagination evidence dan request. | Riwayat analisis dapat dibaca per halaman, termasuk metadata kedaluwarsa melalui pilihan eksplisit. |
| FR23/FR26 | Audit SLR08 dan metadata layanan aman. | GET tidak menjalankan ulang inferensi atau menulis status; metadata tidak membuka execution token/PID/path. |

`config/settings.py` mendaftarkan `reporting` dan `ai_pipeline` tepat satu kali. `config/urls.py` mempertahankan endpoint akun dan memasang kedua modul pada `/api/v1/`. `requirements-ai.txt` menyertakan requirements fondasi; setup yang sudah ada menyelesaikan requirements SLR10 dan AI bersama.

Frontend membaca hasil lewat ReportDetail, lalu menyediakan pemulihan GET request, run terminal dan Report terbaru. Respons mutasi yang body JSON-nya terputus atau hasil gateway-nya belum pasti menjadi `RESPONSE_UNKNOWN`. `REQUEST_RUNNING`/`REQUEST_UNKNOWN` juga menahan tindakan sampai pembacaan keadaan tersimpan. Tidak ada polling, replay POST, worker atau inferensi ulang otomatis.

Runtime sebenarnya selalu memakai model/provider yang dikonfigurasi. Double hanya berada dalam suite pengujian dan tidak dipasang sebagai fallback aplikasi. Konfigurasi AI yang tidak siap tidak menghalangi akun maupun input.

## Dokumen dan bukti

- Petunjuk operasional: satu berkas root `PANDUAN_RUNNING.md`.
- Hasil integrasi: `HASIL_INTEGRASI_v0.2.0.md` dan `evidence/integrasi-v0.2.0/`.
- Laporan awal: `SLR11_Integrasi_dan_Verifikasi_v0.1.md`. Berkas langsung di `evidence/` berasal dari paket 21 Oktober; status dan smoke historisnya tidak dihitung ulang sebagai penerimaan source gabungan.
- Pemulihan pengelola: command `recover_ai_run` dan prosedur A7.5 pada laporan awal. GET pengguna hanya membaca; terminalisasi membutuhkan bukti proses lama berhenti dan fencing token.

UI koreksi, Human Verification, konfirmasi dan submit resmi mengikuti SLR12. Mutu/latensi serta penerimaan lintas fitur mengikuti SLR15. Tidak ada perubahan pada source model, migration fondasi, atau dokumen acuan.

Patch berkas bersama pada laporan awal merujuk isi ZIP SLR11 asli. Konfigurasi pada source gabungan sudah diterapkan; patch historis itu tidak dijalankan kembali.
