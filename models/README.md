# Model dan API SILAR

**Workflow:** periksa identitas aset -> tempatkan arsip kandidat -> baca konfigurasi dan adapter -> lakukan verifikasi pemuatan untuk integrasi SLR11.

## Status aset SLR09

Dokumen ini memperbarui catatan aset SLR09. Model SENA/NARA hasil fine-tuning adalah kandidat integrasi, dengan threshold pilihan pengguna **A (0,95)**. Pemilihan threshold belum merupakan persetujuan mutu akhir atau deployment. Model aktif proyek GEMASTIK tetap mengikuti deployment sebelumnya.

| Komponen | Arsip kandidat | Path dari root repository |
| --- | --- | --- |
| SENA | SILAR_SENA_reviewed_pilot_20261018T044447_926664Z.zip | `models/sena/SILAR_SENA_reviewed_pilot_20261018T044447_926664Z.zip` |
| NARA | SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip | `models/nara/SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip` |

Kedua arsip besar tidak disertakan dalam paket berkas untuk push. Gunakan hasil ekspor yang tercatat pada `MyDrive/SILAR_SLR09/`, dengan nama file tetap. Penempatan di atas adalah lokasi penyerahan artefak; folder hasil ekstraksi dan loader runtime ditentukan pada integrasi SLR11.

Identitas lengkap dan lokasi: `models/slr09/asset_manifest.json`. Identitas bobot mengikuti manifest ekspor Colab; pemeriksaan penyusunan paket ini tidak membuka bobot besar secara langsung.

| Komponen | SHA-256 arsip |
| --- | --- |
| SENA | `144e13d1904f1f4beee56a5ac29fc4fc75cf6a424806ce3c9a0082bf6adf92a3` |
| NARA | `bce9feba0dd2ae4518880708085f44286ae8d1dd7e50f4eb452e36824f967798` |

Arsip historis `SILAR_SENA_v1.zip` dan `SILAR_NARA_v1.zip` adalah rujukan baseline terdahulu. Arsip kandidat hasil fine-tuning tetap memiliki nama versi run-nya sendiri agar hasil dan bobot dapat ditelusuri. Jangan mengubah nama internal model, tokenizer, atau konfigurasi hasil ekspor.

## SILAR SENA

**Nama lengkap:** Situation & Event Narrative Architecture.  
**Peran:** klasifikasi Unified Incident Narrative melalui BERT sequence classification.  
**Label:** FLOOD, EARTHQUAKE, FIRE, ACCIDENT, NON_EVENT.  
**Keluaran:** kategori, confidence, probabilitas dan metadata sumber/versi. Kategori final kartu berasal dari SENA.

Run kandidat `20261018T044447_926664Z` memakai 110 train dan 620 validation hasil review. Accuracy validation 88,06% dan macro F1 88,07%. Validation digunakan memilih checkpoint, sehingga angka tersebut bukan skor test independen. Rincian false NON_EVENT, false event, split dan keterbatasan ada pada laporan SLR09.

## SILAR NARA

**Nama lengkap:** Narrative Analysis & Recognition Architecture.  
**Peran:** ekstraksi token/span dari Unified Incident Narrative melalui BERT token classification.  
**Representasi:** 15 label flat yang dipertahankan, kemudian dipetakan adapter ke tujuh field A4.22. Label dan urutan ID tercatat dalam konfigurasi kandidat.

Field hasil adapter: location_text, time_text, occurred_at, involved_parties, impacts, victims, affected_objects. Informasi yang tidak ditemukan tetap null atau array kosong. Label event NARA tidak menggantikan kategori SENA. REASON tidak menjadi field produk baru.

Run kandidat `20261018T001122_607337Z` memakai 157 train/41 validation. Pada 79 narasi dengan acuan revisi, macro F1 non-O 79,32% dan exact span F1 63,84%; satu kasus DEFERRED tidak dimasukkan. Skor test historis 1.000 narasi turun dari 67,77% menjadi 58,56% dan tetap dilaporkan. Rincian cakupan dan regresi ada pada laporan.

## Adapter, Fusion dan konfigurasi

- Adapter aktif: `silar-adapter-0.4.0`, pada `models/slr09/code/active_nara_adapter/`.
- Guard korban: `silar-victim-guard-0.4.0`; pedoman `nara-role-guideline-0.2`.
- Fusion: `silar-fusion-a4.22-0.1.0`.
- Konfigurasi integrasi: `models/slr09/config/SLR09_Konfigurasi_Integrasi_v0.1.json`.
- Referensi threshold: `SLR09_SENA_20261018T044447_926664Z:reviewed_validation620:cutoff_0.95`.

confidence < 0,95 menghasilkan LOW_CLASSIFICATION_CONFIDENCE; nilai sama dengan threshold tidak menghasilkan alasan tersebut. NON_EVENT tetap memblokir pengiriman. Human Verification tetap wajib dan penerapannya melalui backend menjadi pekerjaan integrasi. Field kosong saja tidak memicu uncertain. Adapter saat ini tidak mengklaim deteksi ambiguity atau konflik ekstraksi secara umum; batas kemampuan tersebut tercatat dalam konfigurasi.

Fusion menggabungkan hasil SENA dan NARA ke data kartu serta alasan uncertain. Fusion tidak menilai kelengkapan wajib semua field, mengajukan pertanyaan adaptif, menentukan validasi manusia, atau mempublikasikan laporan. Notebook Fusion historis dalam paket tetap menjadi rujukan asal. Implementasi aktif menggunakan adapter dan kontrak yang tercatat di atas.

Sembilan pemeriksaan kontrak batas/guard konfigurasi sudah lulus menggunakan fixture buatan. Itu merupakan pemeriksaan fungsi, bukan evaluasi akurasi model baru. Kesiapan pemuatan bersama kedua kandidat pada lingkungan tujuan masih perlu dibuktikan.

## Whisper dan Google Gemini API

Whisper mengubah audio menjadi transkrip. Google Gemini API memahami foto pada rute yang memerlukannya untuk pembentukan narasi terpadu. Keduanya tidak dilatih pada SLR09. SENA dan NARA menerima narasi yang sama; bukti, keluaran komponen dan versi disimpan terpisah sesuai rancangan integrasi.

- Whisper: https://github.com/openai/whisper
- Gemini Image Understanding: https://ai.google.dev/gemini-api/docs/image-understanding

## Sumber, lisensi dan penyimpanan

- Backbone: https://huggingface.co/indolem/indobert-base-uncased ; lisensi MIT tercatat pada pemeriksaan sumber.
- Dataset Semantic Role Labeling Datasets for Crisis Event Version 2: https://data.mendeley.com/datasets/r76v5sjyv2/2 ; DOI 10.17632/r76v5sjyv2.2, CC BY 4.0.
- Dataset raw repository: `data/raw/`.
- Data review SENA: `models/slr09/data/`; NARA: `models/slr09/nara_finetune_frozen/data/`.
- Laporan utama: `docs/ai/slr09/SLR09_Rekap_Notebook_dan_Kesiapan_v0.1.md`.
- Notebook lengkap: `models/slr09/notebooks/`.

Aturan `.gitattributes` repository sudah mencakup `*.zip` melalui Git LFS. Pastikan Git LFS aktif ketika kelompok menambahkan arsip model. SHA manifest menjadi rujukan pemeriksaan identitas arsip, bukan klaim bahwa deployment sudah dilakukan.

## Batas penerimaan

Status SLR09 masih In Review. Review kelompok, target mutu/penerimaan, bukti pemuatan lingkungan tujuan serta Commit SHA/URL perlu dilengkapi sesuai card. Pelatihan dan evaluasi yang sudah selesai tidak perlu diulang untuk menempatkan berkas ini. Pengujian terintegrasi ada pada SLR15, dan deployment pada SLR16.
