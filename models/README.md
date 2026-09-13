# Model dan API SILAR

Dokumen ini mencatat model dan API yang digunakan atau direncanakan untuk diintegrasikan pada SILAR.

## SILAR NARA

**Nama lengkap:** Narrative Analysis & Recognition Architecture  
**Berkas model:** `SILAR_NARA_v1.zip`  
**Peran:** Mengekstrak informasi kejadian dari narasi laporan, seperti jenis kejadian, lokasi, waktu, dampak, korban, objek terdampak, dan informasi pendukung.  
**Arsitektur:** BERT token classification atau semantic role labeling.  
**Backbone:** [indolem/indobert-base-uncased](https://huggingface.co/indolem/indobert-base-uncased)  
**Dataset acuan:** [Semantic Role Labeling Datasets for Crisis Event Version 2](https://data.mendeley.com/datasets/r76v5sjyv2/2)  
**Keluaran:** Informasi kejadian terstruktur untuk diproses oleh SILAR Fusion Engine.

## SILAR SENA

**Nama lengkap:** Situation & Event Narrative Architecture  
**Berkas model:** `SILAR_SENA_v1.zip`  
**Peran:** Mengklasifikasikan narasi laporan ke dalam kategori kejadian.  
**Arsitektur:** BERT sequence classification.  
**Backbone:** [indolem/indobert-base-uncased](https://huggingface.co/indolem/indobert-base-uncased)  
**Kategori keluaran:** `FLOOD`, `EARTHQUAKE`, `FIRE`, `ACCIDENT`, dan `NON_EVENT`.  
**Keluaran:** Kandidat kategori kejadian beserta tingkat keyakinan model.

## SILAR Fusion Engine

**Berkas notebook:** `SILAR_Fusion_Engine.ipynb`  
**Peran:** Menggabungkan hasil SILAR NARA dan SILAR SENA untuk membentuk Incident Card yang konsisten.  
**Keluaran:** Incident Card, status kelengkapan informasi, dan status konflik atau *uncertain* jika bukti belum cukup atau hasil antarkomponen tidak konsisten.

## Whisper Speech to Text

**Peran:** Mengubah rekaman suara pelapor menjadi transkrip teks.  
**Sumber:** [openai/whisper](https://github.com/openai/whisper)  
**Lisensi:** MIT  
**Pemanfaatan:** Transkrip diproses bersama teks pelapor sebelum masuk ke SILAR NARA dan SILAR SENA.

## Google Gemini API

**Peran:** Memahami gambar atau bukti visual dan menghasilkan konteks visual.  
**Dokumentasi:** [Gemini API Image Understanding](https://ai.google.dev/gemini-api/docs/image-understanding)  
**Pemanfaatan:** Konteks visual digunakan sebagai informasi pendukung untuk membentuk Unified Incident Narrative. Gemini tidak menggantikan SILAR NARA, SILAR SENA, atau verifikasi manusia.

## Sumber Dataset

**Nama:** Semantic Role Labeling Datasets for Crisis Event Version 2  
**DOI:** `10.17632/r76v5sjyv2.2`  
**Lisensi:** CC BY 4.0  
**Lokasi repository:** `data/raw/`

## Batasan

SILAR membantu menyusun informasi laporan, bukan memastikan kebenaran kejadian. Semua Incident Card dan informasi hasil AI tetap melalui Human Verification sebelum ditinjau Operator.
