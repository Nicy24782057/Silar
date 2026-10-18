# SLR09 - Penempatan berkas dan model

**Workflow:** unduh paket -> ekstrak -> salin folder docs/models ke root Silar -> tempatkan kedua arsip model -> periksa perubahan -> kelompok melakukan commit/push sendiri.

Paket AI ditempatkan di **models/slr09/** agar folder code/ dapat difokuskan pada aplikasi backend/frontend. Folder model mencakup notebook, kode pelatihan/evaluasi, adapter, konfigurasi dan bukti hasil; isinya tidak terbatas pada bobot. Struktur internal paket kerja dipertahankan sehingga path relatif skrip tetap sesuai.

Jika paket penempatan sebelumnya sudah disalin, pindahkan hanya folder kerja AI dari code/ ke models/ sesuai tabel. Hindari dua salinan paket. Berkas backend/frontend lain tidak perlu dipindahkan.

## Dasar pemeriksaan

Repository: https://github.com/Nicy24782057/Silar  
Commit yang diperiksa: `f7943313fa01eb70c3b41c1ad3efe63d02430f8c`. Struktur repository diperiksa melalui daftar tree GitHub dan isi README/.gitattributes secara baca saja. Penyiapan ini tidak menjalankan git commit, git push, perubahan branch, atau deployment.

## Cara menempatkan paket

1. Ekstrak `SLR09_Berkas_Untuk_Push_v0.1.zip` ke folder sementara.
2. Salin **isi** hasil ekstraksi: folder `docs/` dan `models/` ke root checkout repository Silar milik kelompok. ZIP ini adalah wadah pengiriman; berkas di dalamnya yang disiapkan untuk repository.
3. Untuk snapshot yang diperiksa, satu berkas existing yang diganti adalah `models/README.md`. Versi penggantinya diberikan utuh. Berkas lain di paket merupakan penambahan; berkas proyek di luar daftar paket tidak dihapus.
4. Tempatkan kedua arsip hasil ekspor dari Drive pada path tabel di bawah. Arsip model tidak terdapat dalam paket penyerahan ini.
5. Periksa daftar perubahan dan identitas model sebelum kelompok mencatat commit/push. Aturan Git LFS `*.zip` sudah ada pada repository; Git LFS perlu aktif ketika menambahkan arsip model.

| Path dari root repository | Isi |
| --- | --- |
| `models/slr09/` | Paket kerja lengkap dengan struktur internal dipertahankan. |
| `models/slr09/notebooks/` | Sembilan notebook 00-08, dari pelatihan awal sampai analisis hasil. |
| `models/slr09/code/active_nara_adapter/` | Adapter, guard dan Fusion aktif. |
| `models/slr09/config/` | Identitas kandidat, keputusan A dan konfigurasi 0,95. |
| `models/slr09/data/` | Data review/split SENA dan manifest. |
| `models/slr09/nara_finetune_frozen/data/` | Data review/split NARA dan manifest. |
| `models/slr09/results/` dan `models/slr09/evidence/` | Hasil evaluasi serta bukti proses/pemeriksaan yang sudah tersedia. |
| `docs/ai/slr09/` | Rekap, panduan penempatan dan bukti pemeriksaan paket. |
| `models/README.md` | Penggantian penuh dokumentasi kandidat, versi dan aturan Fusion. |
| `models/slr09/asset_manifest.json` | Lokasi, nama, versi dan hash kedua kandidat. |

Data review ditempatkan bersama paket kerja agar path skrip tetap sesuai. Dataset raw yang sudah ada di `data/raw/` tetap menjadi rujukan sumber; paket ini tidak mengganti dataset raw. Struktur baru di bawah models/slr09, docs/ai/slr09, models/sena dan models/nara adalah susunan penyerahan yang diusulkan dalam paket ini, bukan klaim bahwa folder tersebut sudah terpasang di remote.

## Nama kedua model

**Nama arsip tidak perlu diubah.** Gunakan nama hasil ekspor berikut agar konsisten dengan run, manifest, konfigurasi threshold dan laporan.

| Model | Path arsip yang dituju |
| --- | --- |
| SENA | `models/sena/SILAR_SENA_reviewed_pilot_20261018T044447_926664Z.zip` |
| NARA | `models/nara/SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip` |

Lokasi asal Drive: `MyDrive/SILAR_SLR09/`, menggunakan nama arsip yang sama. Arsip sudah memakai nama SILAR/SENA/NARA; nama historis TanggapMakna dalam notebook sumber dipertahankan untuk penelusuran asal. Nama arsip baru tetap membedakan hasil fine-tuning dari baseline v1.

Nama file internal hasil ekspor model/tokenizer, misalnya `config.json`, `model.safetensors`, `tokenizer_config.json` dan `vocab.txt` jika tersedia, tetap mengikuti hasil ekspornya. Jangan menggantinya menjadi sena.safetensors atau nara.safetensors. Mengganti nama arsip saja tidak mengubah bobot model; jika arsip kelak diganti nama, metadata lokasi/arsip dan rujukan terkait perlu diselaraskan.

## Identitas arsip

- SENA SHA-256: `144e13d1904f1f4beee56a5ac29fc4fc75cf6a424806ce3c9a0082bf6adf92a3`.
- NARA SHA-256: `bce9feba0dd2ae4518880708085f44286ae8d1dd7e50f4eb452e36824f967798`.

Hash berasal dari manifest ekspor Colab dan menjadi pembanding ketika kelompok menempatkan arsip. Bobot besar tidak dibuka ulang untuk menyiapkan paket ini.

## Konfigurasi dan batas pemeriksaan

Pilihan pengguna A (0,95) tersimpan di `models/slr09/config/SLR09_Konfigurasi_Integrasi_v0.1.json`. LOW_CLASSIFICATION_CONFIDENCE berlaku untuk confidence < 0,95; nilai tepat 0,95 tidak mendapat alasan tersebut. NON_EVENT tetap memblokir pengiriman, dan Human Verification wajib. Deteksi ambiguity ekstraksi umum belum diklaim.

Seluruh file paket kerja disalin byte-identik dari paket terverifikasi sebelumnya. Pemeriksaan penempatan tidak menjalankan ulang training atau inferensi model. Notebook 01-07 tidak perlu Run all kembali; notebook 00/08 sudah memiliki keluaran pembacaan hasil tersimpan.

## Status card dan hal yang belum selesai

Paket ini menyiapkan berkas untuk repository, bukan menyatakan SLR09 Done. Target mutu dan penerimaan kelompok, kecukupan evaluasi MVP beserta batas split, keputusan terhadap kemampuan ambiguity, bukti pemuatan kandidat pada lingkungan tujuan, serta catatan review/Commit SHA/URL tetap mengikuti kekurangan yang tercatat pada rekap. Implementasi backend SLR11, penerimaan terintegrasi SLR15 dan deployment SLR16 tidak dijalankan dalam penyiapan ini.

README root repository yang diperiksa masih mencantumkan deskripsi historis tentang kelengkapan/pertanyaan lanjutan. Paket penyerahan ini hanya mengganti `models/README.md`; penyelarasan README root belum dimasukkan agar perubahan di luar berkas SLR09 tetap dapat ditinjau terpisah oleh kelompok.
