# Penuntasan verifikasi SLR14 dan penjelasan pengujian AI

Baseline GitHub: `e0dc88956695170706ce53c2dc53c9086c8f727a`, commit SLR14 yang sudah
tersedia di main pada 30 Oktober 2026. Dokumen dan perintah tambahan ini merupakan
revisi terhadap baseline tersebut. Tidak ada perubahan antarmuka, kontrak API,
model aplikasi, migration, bobot, threshold, layanan inferensi, atau training.

## Arti catatan integrasi AI

Istilah "integrasi AI penuh" pada penjelasan sebelumnya terlalu luas. Terdapat
tiga bukti yang berbeda dan tidak saling menggantikan:

| Pemeriksaan | Yang dibuktikan | Keadaan yang tersedia |
| --- | --- | --- |
| UI dan respons analisis | Loading/progres, pembacaan hasil, tahapan, recovery dan tampilan kartu | Hasil frontend/browser pada paket sebelumnya |
| API → pipeline → penyimpanan | Input/bundle tujuh rute, routing, hasil persisten, referensi sumber, izin, replay, kegagalan dan NON_EVENT | Sembilan tes di ai_pipeline.tests.test_reporting_integration; model/provider adalah test doubles |
| Inferensi nyata dan alur gabungan | Input diproses Whisper/SENA/NARA/Fusion serta Gemini pada rute yang memerlukannya, lalu hasil tersimpan dan dibaca aplikasi | Memerlukan aset/kunci asli dan bukti pada kode yang benar-benar dijalankan; pengujian lintas fitur/performa mengikuti SLR15 |

Sembilan tes API tersebut tidak memakai bobot SENA/NARA/Whisper atau layanan
Gemini asli. Tes memakai model/provider uji yang hasilnya terkendali. Pada mode
PostgreSQL, database, migration, trigger dan lock tetap asli. Lulus sembilan tes
itu bukan bukti mutu prediksi atau inferensi model asli.

Contoh uji nyata teks: teks pengguna → narasi → SENA → NARA → Fusion → hasil
tersimpan → hasil dibaca dan diperiksa Reporter. Audio menambahkan Whisper;
foto atau kombinasi kanal memakai Gemini sesuai kontrak. Informasi yang belum
tersedia tidak diisi dengan tebakan. Konfirmasi dan submit tetap tindakan manusia.

Catatan yang belum terverifikasi berarti bukti penerimaannya belum lengkap.
Catatan tersebut sendiri tidak membuktikan AI aplikasi rusak, dan bukan instruksi
untuk mengganti model atau melakukan training ulang.

## Satu perintah pada komputer aplikasi

Pasang berkas revisi menurut path ke clone yang sudah memuat baseline SLR14.
Gunakan venv, konfigurasi PostgreSQL 16, dan .env yang selama ini dipakai. Dari
folder `code/backend` pada PowerShell:

```powershell
.\.venv\Scripts\python.exe verify_slr14.py --include-pipeline-integration
```

Perintah memeriksa **143 tes native SLR14 + sembilan tes integrasi API = 152 tes**
pada satu database uji baru dengan nama acak. PostgreSQL harus mayor 16 dan role
pengujian memerlukan hak membuat database uji. Database aplikasi tidak dipakai
sebagai database uji; TEST NAME/MIRROR yang menunjuknya tidak digunakan. Semua
migration asli dan guard schema harus aktif. Tidak ada skip, expected failure,
error, atau suite kosong yang dapat menghasilkan PASSED.

Identitas proses OS/psutil juga diperiksa sebelum database uji dibuat ketika
opsi integrasi dipilih. Lingkungan dengan PID tidak terbaca dihentikan dengan
BLOCKED, bukan diberi identitas pengganti. psutil sudah tercantum dalam
requirements-ai.txt SLR11; gunakan lingkungan aplikasi yang telah terpasang.
Tidak ada perubahan pada `ai_pipeline/execution.py` atau sembilan tes aslinya.

Hasil JSON otomatis tersimpan di `docs/slr14/hasil-postgresql/`; terminal
menyebut lokasi tepatnya. Untuk lokasi pilihan:

```powershell
.\.venv\Scripts\python.exe verify_slr14.py --include-pipeline-integration --report hasil-slr14-gabungan.json
```

Perintah lama tanpa flag tetap tersedia untuk 143 tes dasar. Laporan tambahan
menyebut pipeline_integration.requested/discovered_tests, ai_clients=test_doubles,
dan live_ai_inference_exercised=false. PASSED pada perintah gabungan tetap tidak
berarti model/provider asli telah dijalankan.

## Hasil aktual pada lingkungan pengerjaan

- **17 tes guard verifier lulus**: 12 yang sudah ada dan lima tambahan untuk
  batas scope, kelengkapan sembilan tes, serta identitas proses. Unit guard
  memakai objek OS uji secara eksplisit; ini bukan bukti PostgreSQL berjalan.
- Perintah dasar: **BLOCKED**, 143 ditemukan, 0 dijalankan.
- Perintah gabungan: **BLOCKED**, 152 ditemukan, sembilan tes integrasi terdeteksi,
  0 dijalankan. Tidak ada server PostgreSQL yang dapat diakses.
- Pemeriksaan identitas proses OS gagal pada lingkungan QA ini; aset model asli
  juga tidak tersedia. Tidak ada inferensi nyata atau panggilan Gemini baru.
- Runtime pemulihan proses dan tes integrasi asli tidak diubah untuk meluluskan
  lingkungan QA. Tidak ada fallback SQLite pada perintah native.

Bukti: `bukti/penuntasan-guard-verifikasi.txt`, `penuntasan-native-dasar.json`,
`penuntasan-native-dan-integrasi-api.json`, dan `penuntasan-lingkungan.json`.
Hasil lama tetap disimpan sebagai riwayat. Bukti frontend/backend komponen dari
paket sebelumnya tidak dinyatakan sebagai eksekusi baru pada revisi ini.

## Melengkapi bukti model asli

Pada komputer yang menjalankan aplikasi, pertahankan aset SENA/NARA sesuai
manifest/adapter SLR09, Whisper lokal untuk audio, decoder yang diperlukan,
serta konfigurasi Gemini untuk foto/kombinasi kanal. Model tidak diunduh ulang
oleh perintah verifikasi di atas.

Uji T, A, I, TA, TI, AI dan TAI menggunakan sumber uji yang berhak digunakan.
Catat commit, versi model, rute/run, hasil tersimpan, kesesuaian referensi sumber,
waktu dan kegagalan aktual. Jangan menyimpulkan mutu model atau kapasitas dari
waktu fixture. Pengujian end-to-end dan pengukuran penerimaan terintegrasi berada
pada SLR15 menurut pemetaan proyek. Tindakan model yang menghasilkan biaya atau
membuka data eksternal tetap mengikuti informasi pemrosesan pada aplikasi.

Status In Review dapat membawa catatan terbuka ini. Penuntasan penerimaan native
memerlukan laporan PASSED dari lingkungan PostgreSQL 16 yang benar; hasilnya
belum dapat dinyatakan selesai hanya dari lingkungan QA yang BLOCKED.
