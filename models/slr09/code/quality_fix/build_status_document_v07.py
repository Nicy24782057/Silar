"""Write current status from executed evidence; never turn diagnostic pass into Done."""
import argparse
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
def pct(v):return f'{v*100:.2f}%'.replace('.',',')

def build(work,output):
    d=read(work/'report_data_v07.json');e=read(work/'quality_diagnostics_v07/evaluation.json')
    c=d['fresh'];h=d['latest_development'];s=read(work/'training_matched_v07/best_selection.json')
    fresh_errors=read(work/'quality_diagnostics_v07/new50_evaluation.json')['errors']
    lock=read(ROOT/'config/quality_candidate_asset_lock_v0.7.json')['models']['sena']
    text=f'''# SLR_09: hasil terbaru v0.7, 19 Oktober 2026

**Status mutu tetap In Review.** Perbaikan SENA dan verifikasi sudah dijalankan di CPU ini, tanpa meminta pengguna mengulang di laptop. Diagnostik baru 50 narasi memenuhi target klasifikasi, tetapi regresi lama masih gagal pada NON_EVENT dan pasangan simulasi. Development manusia lama juga belum memenuhi recall NON_EVENT. Target tidak diturunkan. Tidak ada penerimaan mutu, push, perubahan Kanban, atau deployment.

## Hasil kandidat terakhir

| Data | Peran dan asal acuan | Macro F1 SENA | Recall NON_EVENT | Recall kejadian minimum | Hasil |
| --- | --- | ---: | ---: | ---: | --- |
| 146 narasi manusia lama | Development untuk pemilihan, bukan test akhir | {pct(h['macro_f1'])} | {pct(h['non_event_recall'])} | {pct(h['min_event_recall'])} | Recall NON_EVENT belum 90% |
| 74 narasi tambahan lama | Usulan asisten, sudah dilihat dan dipakai memilih | {pct(d['history'][-1][2])} | {pct(d['history'][-1][3])} | {pct(d['history'][-1][4])} | Target klasifikasi development terpenuhi |
| 50 narasi manusia pilot lama | Regresi yang sudah diketahui | {pct(e['sena']['macro_f1'])} | {pct(e['sena']['per_class']['NON_EVENT']['recall'])} | 100,00% | Recall NON_EVENT dan kontras simulasi belum terpenuhi |
| 50 narasi baru v0.7 | Usulan asisten dibekukan sebelum pelatihan, belum direview manusia | {pct(c['macro_f1'])} | {pct(c['non_event_recall'])} | {pct(c['min_event_recall'])} | Target diagnostik klasifikasi terpenuhi, bukan penerimaan manusia |

Target klasifikasi tetap macro F1 ≥85%, recall NON_EVENT ≥90%, serta recall masing-masing kelas kejadian ≥80%. Dua himpunan 50 yang berbeda tidak boleh dibandingkan sebagai kenaikan pada data yang sama. Seluruh 74 narasi lama kini development. Lima puluh baru v0.7 tidak dipakai untuk training, pemilihan checkpoint atau fitting bias. Jika nanti hasilnya dipakai memperbaiki model, set tersebut juga harus dipindahkan ke development.

### Dua kesalahan pada regresi manusia 50

| ID | Narasi | Acuan manusia | Prediksi | Confidence |
| --- | --- | --- | --- | ---: |
'''
    for row in e['sena']['errors']:text+=f"| {row['id']} | {row['text']} | {row['gold']} | {row['prediction']} | {pct(row['confidence'])} |\n"
    text+='''
Kandidat v0.5 sebelumnya lulus seluruh target pada 50 narasi ini, tetapi gagal pada diagnostik tambahan. Kandidat v0.7 memperbaiki banyak konteks nyata, namun mengembalikan dua false event lama. Regresi ini dicatat sebagai kegagalan, bukan disembunyikan oleh skor pada set baru. Model v0.7 belum layak menggantikan model yang dinyatakan lolos mutu.

### Dua kesalahan pada diagnostik baru v0.7

| ID | Acuan usulan asisten | Prediksi | Confidence | Konteks |
| --- | --- | --- | ---: | --- |
'''
    for row in fresh_errors:text+=f"| {row['id']} | {row['gold']} | {row['prediction']} | {pct(row['confidence'])} | {row['family']} |\n"
    text+=f'''
Semua 50 narasi baru beserta prediksi tersedia pada tab **Diagnostik Baru**. Acuannya bukan label manusia. Dua kesalahan itu berada di bawah cutoff 0,95 dan tetap memerlukan Human Verification; fakta ini tidak menghapus kegagalan klasifikasi atau membuktikan probabilitas terkalibrasi.

## NARA dan field

NARA tidak dilatih ulang. Prediksi token, skor NARA, dan skor field dihitung kembali dengan bobot yang sama. Skor NARA serta field persis sama dengan hasil v0.5 pada 50 acuan manusia yang sama.

| Metrik | Hasil pada regresi 50 | Target |
| --- | ---: | ---: |
| NARA macro F1 seluruh 14 label non-O | 88,51% | ≥75% |
| NARA exact span F1 | 86,72% | ≥60% |
| Ketepatan field beracuan nonkosong | 175/191 = 91,62% | ≥80% |
| Isi berlebih pada field beracuan kosong | 2/159 = 1,26% | ≤5% |

Guard korban, penggabungan dampak/objek, filter negasi lokal, dan fallback waktu dari v0.5 dipertahankan. Helper legacy tidak berubah: SHA-256 `06275b3aa338718689fba66984626754e6b34739156f65e378ceaad4b06bfa9f`. Kategori tetap dari SENA, NARA FALSE-EVENT tidak menimpanya. NON_EVENT memblokir, Human Verification selalu wajib, field kosong tidak otomatis uncertain, dan confidence rendah hanya bila **<0,95**. Tidak ada klaim kalibrasi probabilitas atau detektor ambiguitas umum.

## Percobaan yang dijalankan

1. **v0.6, penambahan cakupan konteks.** Warm start dari eksperimen CPU v0.5 sebelum bias +2,1. Training 1.128 contoh: manusia584, tambahan terdahulu64, dan usulan baru480. Development manusia146 dan asisten128. Tambahan label bukan acuan manusia. Penyesuaian intercept pada development menghasilkan bias total +3,4; diagnostik baru v0.6 hanya F1 79,40% dan recall kejadian terendah 60%. Bias besar juga memblokir kejadian nyata. Hasil gagal dan analisis bias tetap disimpan.
2. **v0.7, pasangan dengan isi dampak yang sama.** Training 1.160 contoh: manusia584, tambahan terdahulu64, dan 512 contoh dalam 256 pasangan asisten. Positif/negatif memuat kata dampak yang sama, dibedakan oleh konteks kejadian nyata, fiksi, bantahan, prediksi, atau latihan. Loss pasangan menjaga pemisahan konteks; bobot loss asisten 0,5. Empat layer akhir, pooler, dan classifier dilatih. Bias manual +1,5 dari warm start dihapus sebelum gradient. Grid bias tambahan dibatasi -0,5 sampai +0,5. Pemilihan tetap menilai target yang sama pada kedua development, termasuk NON_EVENT manusia146; target itu belum tercapai.
3. **Early stopping.** Maksimal tiga epoch, berhenti setelah dua karena hasil development memburuk. Checkpoint terpilih epoch **{s['epoch']}**, bias manual tambahan **{s['bias']:+.1f}**. Tidak ada penyesuaian parameter sesudah hasil diagnostik v0.7 dibuka.

730 label manusia terdahulu tetap memakai pembagian manusia584 training dan manusia146 development yang sama. Validation620 lama sudah menjadi sumber pengembangan. Keanggotaan pelatihan awal baseline belum terverifikasi. Diagnostik baru v0.7 berisi sepuluh contoh per kategori, seluruhnya narasi sintetis usulan asisten. Pemeriksaan overlap adalah kecocokan teks ternormalisasi, bukan bukti keterwakilan populasi atau independensi semantik/template.

Kesalahan pada tweet lama mencakup metafora seperti “banjir dukungan”, kegiatan antisipasi, statistik, pantun, serta batas laporan kejadian tertentu. Sebagian teks historis dan sosial diberi label kelas kejadian dalam data terdahulu; definisinya perlu dipastikan reviewer agar konsisten dengan cakupan MVP. Label manusia tersebut tidak diganti otomatis untuk menaikkan skor.

## Identitas, verifikasi, dan notebook

Kandidat pengembangan: `{lock['model_id']}`. Arsip `{lock['archive_name']}` terpisah dari sumber Git.

- SHA-256 arsip SENA: `{lock['archive_sha256']}`.
- SHA-256 bobot SENA: `{lock['files']['model.safetensors']}`.
- SHA-256 diagnostik beku v0.7: `{d['frozen_diagnostic_sha256']}`.
- Konfigurasi `config/SLR09_Konfigurasi_Integrasi_v0.4.json`, lock `config/quality_candidate_asset_lock_v0.7.json`, runtime kandidat `0.5.0`.
- Ekspor direproduksi lewat bobot yang benar-benar dimuat. Semua label development cocok, selisih probabilitas berada dalam toleransi 1e-5. Skor tersimpan dihitung ulang dan cocok. **71/71** tes kontrak/runtime lulus.
- Python3.12.14, torch2.11.0+cpu, transformers4.57.1, tokenizers0.22.1, safetensors0.8.0, numpy2.1.3. Dua thread CPU. Peak RSS inferensi bersama 1.233.473.536 byte pada lingkungan ini, bukan bukti otomatis kapasitas VM produksi.
- Satu penyalinan warm start yang terpotong ditolak pemeriksaan hash **sebelum gradient**. Salinan diperbaiki dan keenam hash diverifikasi sebelum training nyata. Kegagalan precheck tetap ada pada evidence; tidak dihitung sebagai training berhasil.

| Notebook tambahan yang benar-benar dijalankan | Isi |
| --- | --- |
| `13_Perbaikan_Konteks_SENA_CPU_v0.6.ipynb` | Pelatihan cakupan konteks v0.6. |
| `13b_Penyeimbangan_Kelas_SENA_v0.6.ipynb` | Fitting bias pada development, bukan training gradient tambahan. |
| `14_Verifikasi_SENA_dan_Regresi_SLR09_v0.6.ipynb` | Ekspor, tes, reproduksi development, regresi50, diagnostik24+50. |
| `15_Latihan_Pasangan_Konteks_SENA_v0.7.ipynb` | Pelatihan berpasangan dan early stopping. |
| `16_Verifikasi_Kandidat_SLR09_v0.7.ipynb` | Ekspor, 71 tes, reproduksi development, regresi50, diagnostik74+50. |

Sumber dan salinan `_executed.ipynb` berisi output nyata. Sel Python dieksekusi berurutan melalui CPython cell executor dan metodenya dicatat pada metadata; ini bukan klaim eksekusi kernel Jupyter asli. Notebook 11, 11b dan 12 tetap sebagai bukti run terdahulu di sini; notebook 09 dan 10 adalah bukti historis pengguna. Snapshot runtime/config v0.6 dan v0.7 dipisahkan supaya identitas run lama tetap dapat diaudit.

## Langkah agar dapat Done

1. **Tinjau 40 baris pada Review Data.** Isi reviewer B4, pilih kelas pada kolom D, lalu status dan alasan pada E–F. Semuanya masih PENDING dalam sumber yang tersedia. Ini memastikan definisi label untuk pengembangan, bukan meminta menjalankan ulang notebook. Importer menolak workbook kosong dan tidak menganggap data yang sudah dilihat sebagai test akhir baru.
2. **Perbaiki cakupan NON_EVENT tanpa merusak kejadian nyata.** Fokus pada simulasi pendek, perkiraan, metafora, dan narasi sosial yang tidak melaporkan peristiwa. Gunakan label yang konsisten untuk latihan/seleksi; jangan menambah aturan global kata “simulasi” yang memblokir kejadian nyata saat latihan. Regresi lama serta development manusia belum memenuhi target sehingga kandidat tidak dipromosikan.
3. **Penerimaan baru setelah kandidat dibekukan.** Acuan kategori, tujuh field dan token harus direview manusia sebelum inferensi. Cakupan MVP tetap minimal10 per kategori, semua14 role non-O, serta kontras simulasi/latihan dan kejadian nyata. Kit penerimaan lama terikat kandidat/kode terdahulu; binding serta acuan baru perlu dibuat untuk kandidat yang akan diajukan. Seluruh target dan keputusan penerimaan reviewer diperlukan. Eksekusi model dapat dilakukan di sini.

Menambah epoch terus-menerus, memakai diagnostik yang sama untuk tuning, atau menurunkan target sesudah melihat hasil tidak menyelesaikan masalah ini. Early stopping dan data terpisah sudah diterapkan, tetapi angka sintetis yang memenuhi target tidak cukup untuk memberi Done. Penerimaan mutu belum disetujui.

## Rekap perubahan dan push nanti

Tidak perlu mengunggah ulang seluruh repository. Paket merupakan overlay terhadap paket v0.5 yang kita siapkan, belum pembandingan dengan ZIP GitHub pengguna. Cocokkan basis melalui manifest sebelum penggabungan akhir. Belum ada remote push.

| Kelompok | Path relatif repository |
| --- | --- |
| Loader dan pengujian kandidat | `models/slr09/code/active_nara_adapter/slr09_candidate_runtime.py`, `models/slr09/code/tests/test_candidate_runtime.py` |
| Skrip latihan, verifikasi dan pelaporan | Berkas baru pada `models/slr09/code/quality_fix/` menurut manifest |
| Konfigurasi kandidat pengembangan | Konfigurasi v0.3/v0.4 dan lock v0.6/v0.7 pada `models/slr09/config/` |
| Notebook dan output nyata | Notebook13,13b,14,15,16 dan pasangan `_executed.ipynb` |
| Data, hasil dan jejak audit | Berkas baru `data/`, `evidence/quality_fix_v06/`, `evidence/quality_fix_v07/`, `results/quality_fix_v07/` |
| Status dan catatan lanjut | `SLR09_STATUS_v0.7.md` dan `CHECKPOINT_v0.7.md` |

Arsip bobot terpisah masih eksperimen. NARA tidak perlu diunggah ulang. Runtime pengembangan baru tidak berarti kandidat disetujui untuk produksi. Venv, cache, bytecode, dan direktori ekstraksi bobot tidak masuk paket kode. Riwayat konfigurasi dan bobot lama dipertahankan.

Perbandingan ZIP sebelumnya tetap ditunda sesuai permintaan. Dua commit tracking SLR_08 dan suffix nama lokal `(3)` tetap dikecualikan dari temuan audit.
'''
    output.write_text(text,encoding='utf-8');print(str(output));return text

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.work,a.output)
