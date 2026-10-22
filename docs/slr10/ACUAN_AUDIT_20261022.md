# SLR10 — Rincian Revisi setelah Audit dan Penyelarasan SLR11

Tanggal: 22 Oktober 2026  
Versi dokumen: 0.1  
Paket yang diaudit: `SLR_10_SILAR_Final_v1.0.0.zip`  
Status: daftar tindak lanjut audit; perubahan dan pengujian ulang belum dinyatakan selesai.

## 1. Keputusan dan acuan

Format audio sudah tercantum pada **SLR11 — Integrasi Pipeline AI dan Hasil Verifikasi**, bagian **Konfigurasi dan aset**, baris Audio: MP3, WAV PCM, WebM/Opus, serta M4A/MP4-AAC tanpa video. Daftar tersebut selaras dengan dokumen **SILAR — Kesepakatan Implementasi SLR10 dan SLR11**, bagian 2, dan decoder `ai_pipeline/audio.py` pada paket SLR11 yang diperiksa.

Dengan demikian, revisi utama audio dilakukan pada **SLR10**, yaitu validator unggahan, pilihan berkas, recorder, pesan panduan, pengujian, dan dokumentasinya. Dukungan format SLR11 tidak perlu diperluas menjadi OGG, ALAC, atau Vorbis untuk menyesuaikan ketidaksesuaian paket SLR10 saat ini.

Acuan pekerjaan:

1. SILAR Technical Reference v0.3: A6 untuk kontrak API/schema, A7.3 untuk batas input, A7.4–A7.5 untuk idempotensi/pemulihan, dan A7.6–A7.8 untuk cache, verifikasi operasional, serta Digital Awareness.
2. SILAR — Kesepakatan Implementasi SLR10 dan SLR11: bagian 2–6 untuk audio, pembagian endpoint, revision/error, berkas bersama, dan pengujian integrasi.
3. SLR11 — Integrasi Pipeline AI dan Hasil Verifikasi v0.1 beserta kode implementasinya.
4. Card SLR10 yang diberikan pemilik proyek serta rancangan SLR07, terutama layar akun, RP01–RP03, dan UM02.

Dokumen verifikasi SLR11 tanggal 21 Oktober masih mencatat keadaan pengujian awal penyusun. Pengujian lanjutan di Windows telah dilaporkan pemilik proyek dalam sesi pendampingan, termasuk 15 tes database dan contoh analisis nyata. Hasil tersebut dicatat sebagai pengujian lanjutan tersendiri; alur frontend SLR10 yang baru tetap memerlukan verifikasi gabungan.

## 2. Ringkasan prioritas dan tanggung jawab

| ID | Prioritas | Tindak lanjut | Penanggung jawab |
| --- | --- | --- | --- |
| R10-01 | P1 — penghambat integrasi | Samakan dukungan audio dari frontend sampai validator unggahan dengan SLR11. | Pelaksana SLR10; pelaksana SLR11 memverifikasi pembacaan bukti hasil unggah. |
| R10-02 | P1 — penghambat integrasi | Hilangkan pertentangan versi Pillow dan sesuaikan installer. | Pelaksana SLR10 memperbaiki paket; versi gabungan diselaraskan bersama pelaksana SLR11. |
| R10-03 | P2 — pemeriksaan paket | Perbaiki pembacaan LF/CRLF pada skrip pemeriksaan prototype SLR07 yang dibundel. | Pelaksana SLR10 menyesuaikan paket yang diserahkan; koordinasikan perubahan sumber bersama pengelola SLR07. |
| R10-04 | P2 — penyajian hasil | Tampilkan peringatan normalisasi NARA secara ramah tanpa mengubah arti uncertain. | Pelaksana SLR10 untuk tampilan; pelaksana SLR11 menyediakan struktur hasil yang konsisten. |
| R10-05 | Syarat verifikasi penyerahan | Jalankan regresi, verifikasi integrasi pada lingkungan tujuan, dan perbarui bukti sesuai hasil aktual. | Pelaksana SLR10 dan SLR11 pada bagian masing-masing serta uji bersama. |

R10-01 dan R10-02 diselesaikan sebelum paket dinyatakan siap digabung. R10-03 merupakan masalah reproduksi pemeriksaan prototype. R10-04 merupakan penyempurnaan tampilan hasil saat integrasi, bukan perubahan kontrak atau model AI.

## 3. R10-01 — Penyelarasan audio

### Temuan yang dibuktikan

Audit menggunakan audio sintetis pendek dengan codec sebenarnya, kemudian memanggil validator SLR10 dan decoder SLR11. Ini pengujian decoding, bukan pengujian Whisper atau akurasi kejadian.

| Berkas/codec uji | SLR10 saat audit | SLR11 saat audit | Target revisi SLR10 |
| --- | --- | --- | --- |
| WAV PCM | Diterima | Diterima | Pertahankan dukungan PCM. |
| MP3 | Diterima | Diterima | Pertahankan. |
| M4A/AAC | Diterima | Diterima | Pertahankan, batasi codec ke AAC. |
| WebM/Opus | Diterima | Diterima | Pertahankan, batasi codec ke Opus. |
| MP4/AAC tanpa video | Ditolak | Diterima | Tambahkan dukungan `.mp4` audio AAC tanpa video. |
| OGG/Opus | Diterima | Ditolak | Tolak pada pilihan/validasi unggahan; keluarkan dari fallback recorder. |
| M4A/ALAC | Diterima | Ditolak | Tolak codec ALAC. |
| WebM/Vorbis | Diterima | Ditolak | Tolak codec Vorbis. |

Dampak saat ini: sebagian bukti dapat tersimpan sebagai audio valid pada SLR10, tetapi gagal diproses ketika dibaca pipeline SLR11.

### Berkas yang perlu ditinjau dan diperbaiki

| Berkas, relatif terhadap root repository | Revisi |
| --- | --- |
| `code/backend/reporting/media.py` | Sesuaikan profil container/codec dan validasi MIME/stream. |
| `code/frontend/src/domain.js` | Tambahkan `.mp4`, hapus `.ogg`, dan samakan pesan format yang diterima. |
| `code/frontend/src/components/AudioRecorder.vue` | Hapus fallback OGG; pilih format rekaman yang sesuai kesepakatan. |
| `code/frontend/src/views/DraftView.vue` | Sesuaikan atribut `accept`, panduan audio, serta pesan kegagalan. |
| `code/backend/reporting/tests/test_media.py` | Tambahkan regresi kontrak format, termasuk kasus yang sebelumnya berbeda. |
| `code/backend/reporting/tests/test_api.py` | Buktikan unggahan format valid dan penolakan format/codec yang tidak didukung. |
| `code/frontend/tests/domain.test.js` | Perbarui ekspektasi ekstensi; OGG tidak lagi dinyatakan sebagai format yang diterima. |

### Aturan implementasi

- Format target: `.mp3` dengan MP3; `.wav` dengan PCM; `.webm` dengan Opus; `.m4a` atau `.mp4` dengan AAC dan tanpa video.
- Validasi isi/container/codec serta keberhasilan decode pada backend. Ekstensi atau MIME client saja tidak cukup untuk menerima berkas.
- Samakan kebijakan stream video dengan decoder SLR11, termasuk perlakuan stream gambar/cover apabila berkas memilikinya, agar unggahan tidak diterima oleh satu tahap lalu ditolak tahap berikutnya.
- Pertahankan batas satu audio per bundle, 10 MiB per audio, durasi lebih dari nol dan maksimal 120 detik, serta total bundle maksimal 25 MiB termasuk byte teks.
- Simpan byte audio asli beserta metadata/hash. Decoding/resampling internal mono 16 kHz untuk Whisper tetap menjadi tanggung jawab SLR11.
- Validator SLR10 boleh tetap menggunakan FFmpeg/ffprobe dan SLR11 menggunakan PyAV, selama menerima/menolak berkas yang sama sesuai kontrak. SLR10 tetap dapat diuji mandiri tanpa memuat bobot model AI.
- Decoder yang belum tersedia dibedakan dari media tidak valid; pertahankan pesan dan kode kegagalan aman sesuai kontrak yang berlaku.

### Perilaku recorder yang diharapkan

1. Periksa dukungan `audio/webm;codecs=opus` melalui `MediaRecorder.isTypeSupported()`.
2. Jika tidak didukung, periksa pilihan MP4/AAC yang didukung browser. MIME MP4 generik hanya digunakan bila keluaran sebenarnya dapat divalidasi sebagai AAC tanpa video.
3. Jika tidak ada pilihan yang sesuai atau rekaman gagal, tampilkan penjelasan dan tetap sediakan unggah audio/kanal lain.
4. Nama berkas, ekstensi, dan MIME mengikuti hasil rekaman sebenarnya. Jangan mengganti nama WebM/OGG menjadi MP3 sebagai pengganti konversi.
5. Rekaman browser tidak wajib diubah menjadi MP3. MP3 tetap didukung sebagai berkas unggahan.

### Kriteria verifikasi

- [ ] WAV PCM, MP3, WebM/Opus, M4A/AAC, dan MP4/AAC tanpa video diterima melalui API unggahan dan dapat dibaca `ai_pipeline.sources.load_sources()`.
- [ ] OGG/Opus, M4A/ALAC, WebM/Vorbis, serta MP4 yang memiliki video ditolak secara konsisten sebelum dinyatakan sebagai bukti audio valid.
- [ ] Ekstensi palsu, MIME tidak sesuai, audio rusak/kosong, ukuran berlebih, dan durasi berlebih ditolak dengan respons aman.
- [ ] File input dan panduan UI menampilkan format yang sama dengan backend; batasan codec tetap dijelaskan meskipun pemilih berkas browser menyaring berdasarkan ekstensi.
- [ ] Recorder pada browser sasaran menghasilkan berkas yang lolos unggah dan pembacaan SLR11; fallback serta penolakan izin mikrofon memiliki pesan yang dapat ditindaklanjuti.

## 4. R10-02 — Dependensi Pillow dan installer

### Temuan

`code/backend/requirements.txt` pada SLR10 mengunci `Pillow==12.3.0`. `code/backend/requirements-ai.txt` pada SLR11 mengunci `Pillow==13.0.0` dan juga menyertakan `requirements.txt`. Resolver menolak gabungan dua pin yang berbeda ini.

`tools/install_slr10.py` juga masih menganggap 12.3.0 sebagai satu-satunya pin Pillow yang sesuai dan merencanakan penambahan versi tersebut bila belum ada pada requirements dasar.

### Revisi yang diminta

1. Gunakan **Pillow 13.0.0 sebagai baseline penyelarasan**, sesuai pin SLR11 yang telah digunakan pada pengujian sebelumnya. Uji ulang decoder gambar SLR10 pada versi itu sebelum menyatakan kompatibel.
2. Sesuaikan `code/backend/requirements.txt` dan logika `tools/install_slr10.py`; installer tidak boleh memasukkan kembali 12.3.0 atau menyebabkan downgrade dari baseline gabungan.
3. Pastikan `requirements-slr10.txt` dan `requirements-ai.txt` dapat di-resolve bersama. Penempatan akhir pin mengikuti penyatuan dependensi bersama; jangan meninggalkan pin yang bertentangan pada jalur include.
4. Pertahankan pemeriksaan konflik lokal, rencana perubahan, dan backup installer. Perubahan konfigurasi dilakukan terarah, dengan mempertahankan pekerjaan `ai_pipeline`, koneksi database, secret, serta aset model yang sudah ada.
5. Instalasi baru dan pemasangan ke repository SLR11 yang sudah berjalan harus sama-sama diperiksa. Jangan menjadikan penghapusan venv atau pembuatan ulang database sebagai penyelesaian konflik pin.

### Kriteria verifikasi

- [ ] Resolver dapat memasang kedua berkas requirements dalam satu lingkungan yang sama.
- [ ] Validasi PNG/JPEG SLR10 lulus pada versi Pillow gabungan.
- [ ] Installer tidak memaksakan 12.3.0 dan tetap menolak perubahan lokal yang tidak aman untuk ditimpa.
- [ ] Uji pemasangan membuktikan `.env`, `ai_pipeline`, media privat, dan aset model tetap dipertahankan.

## 5. R10-03 — Pemeriksaan prototype SLR07 pada LF/CRLF

### Temuan

Perintah `node docs/uiux/tools/check.mjs` pada paket yang diaudit berhenti dengan `SyntaxError: Cannot use import statement outside a module`. Skrip menghapus baris import menggunakan pola yang mengharapkan `;\n`, sedangkan `prototype/app.mjs` pada paket memakai `;\r\n`.

Ini temuan pada harness pemeriksaan prototype yang dibundel. Build Vue SLR10 berhasil; kegagalan ini sendiri tidak membuktikan aplikasi Vue gagal dirender.

### Revisi yang diminta

- Perbaiki pembacaan/penghapusan baris import pada `docs/uiux/tools/check.mjs` agar menerima LF dan CRLF. Normalisasi akhir baris dalam teks yang dibaca harness, atau pola yang menerima `\r?\n`, dapat digunakan.
- Periksa pola serupa pada `docs/uiux/tools/review-check.mjs` dan `docs/uiux/tools/audit-check.mjs` agar pemeriksaan paket konsisten.
- Contoh pola untuk baris import tunggal yang ada pada prototype saat ini:

```javascript
const src = fs.readFileSync(path.join(assetPath, 'app.mjs'), 'utf8')
  .replace(/^import .*?;\r?\n/, '');
```

- Jalankan pemeriksaan pada sumber dengan LF dan CRLF. Catat jumlah aktual yang berhasil; jangan menyalin jumlah kelulusan historis sebagai bukti paket baru.
- Koordinasikan perubahan pada sumber SLR07 yang ikut dibundel agar tidak muncul dua salinan harness dengan perilaku berbeda.

### Kriteria verifikasi

- [ ] Ketiga skrip pemeriksaan yang disertakan dapat dijalankan sampai selesai pada salinan paket yang diserahkan.
- [ ] Perbedaan LF/CRLF tidak menyebabkan import tertinggal dalam konteks VM.
- [ ] Pemeriksaan prototype tetap dibedakan dari pengujian visual/browser frontend Vue.

## 6. R10-04 — Peringatan normalisasi NARA pada tampilan hasil

### Temuan dan kedudukan

`reporting.serializers.run_data()` sudah menyertakan `normalization_warnings`. Akan tetapi, `code/frontend/src/components/AnalysisResult.vue` baru menampilkan kategori, confidence, field kartu, serta `uncertain` dan alasannya.

Pada contoh integrasi sebelumnya terdapat usulan dampak NARA yang perlu diperiksa meskipun confidence SENA tinggi dan `uncertain` bernilai false. Karena itu, peringatan normalisasi berguna untuk membantu pengguna membaca hasil awal. Ini penyempurnaan penyajian hasil integrasi; bukan klaim adanya kontrak wajib baru untuk seluruh perilaku UI.

### Revisi yang diminta

- Ambil peringatan dari `detail.latest_run.nara.normalization_warnings` bila tersedia dan sesuai dengan hasil yang sedang ditampilkan.
- Tampilkan label ramah, misalnya **“Usulan dampak perlu diperiksa”** untuk `INFORMATION_AS_IMPACT_SUGGESTION`, dengan konteks field yang relevan. Gunakan pemetaan aman untuk kode yang dikenal serta pesan umum untuk kode yang belum dipetakan.
- Nilai kosong atau hasil yang belum tersedia tidak menyebabkan error render.
- Jangan mengubah `uncertain` menjadi true hanya karena ada peringatan normalisasi. Makna flag, threshold SENA, dan keputusan Fusion tetap mengikuti baseline SLR09/SLR11.
- Penyajian ini tidak menjalankan ulang AI, mengubah hasil mentah, melakukan konfirmasi otomatis, atau menambah endpoint Human Verification ke SLR10.

### Kriteria verifikasi

- [ ] Peringatan tetap terlihat ketika `uncertain=false` dan daftar peringatan tidak kosong.
- [ ] `uncertain=true` dan peringatan normalisasi dapat ditampilkan bersama sebagai informasi yang berbeda.
- [ ] Daftar kosong serta NARA yang belum tersedia dapat dirender dengan aman.
- [ ] Kartu dan peringatan yang ditampilkan merujuk sumber/run yang sesuai; hasil baru atau run gagal tidak mencampurkan keterangan hasil lama tanpa penjelasan.

## 7. R10-05 — Pengujian ulang dan bukti penyerahan

### Hasil audit yang sudah tersedia sebelum revisi

| Pemeriksaan | Hasil | Batas bukti |
| --- | --- | --- |
| Tes backend reporting | 31 lulus. | SQLite khusus komponen; tidak menguji trigger/lock PostgreSQL. |
| Tes frontend/PWA | 11 lulus. | Tes otomatis helper/kontrak frontend dan service worker. |
| Build produksi Vue | Berhasil. | Membuktikan source dapat dibangun; tidak menggantikan review visual. |
| Penghubung tujuh kanal | T, A, I, TA, TI, AI, TAI berhasil dari API input/bundle ke loader SLR11 pada contoh yang diuji. | Memakai database komponen serta bukti sintetis; tidak menjalankan inferensi model. |
| Serialisasi hasil | Run dan Card SLR10 cocok dengan helper SLR11 pada graph uji tersimpan. | Graph sintetis; bukan prediksi AI. |
| Matrix codec audio | Ketidaksesuaian pada bagian 3 direproduksi dengan berkas yang benar-benar didekode. | Bukan pengujian kualitas transkripsi. |
| Resolver Pillow | Gabungan pin 12.3.0 dan 13.0.0 ditolak. | Bukti penghambat dependensi, bukan hasil perbaikannya. |
| Pemeriksaan prototype | Harness utama gagal pada import dengan CRLF. | Berbeda dari hasil build Vue. |

Paket SLR10 juga mencatat 20 skenario browser dari lingkungan penyusunnya. Pada audit ini, review visual browser belum berhasil diulang. Hasil historis itu dipertahankan dengan keterangan lingkungan dan versi yang diuji.

### Urutan verifikasi setelah revisi

1. Selesaikan R10-01 dan R10-02, lalu jalankan regresi media serta resolusi dependensi gabungan.
2. Jalankan tes frontend dan build; lanjutkan pemeriksaan harness prototype setelah R10-03.
3. Gabungkan registrasi `reporting` dan `ai_pipeline` pada settings/URL yang sama sambil mempertahankan fondasi SLR08. Semua endpoint tetap mengikuti A6.
4. Jalankan regresi backend pada PostgreSQL 16 dengan migrasi dan trigger asli. Pada instalasi pemilik proyek, koneksi yang sudah berhasil adalah port 5433; pertahankan konfigurasi lokal yang benar.
5. Uji melalui frontend: login → buat/lanjutkan draft → simpan teks/unggah/rekam → baca bukti sebelum bundle → pilih bukti → buat bundle → analisis → baca draft kartu tersimpan.
6. Jalankan tujuh rute dengan Whisper/Gemini sesuai kanal, menggunakan contoh yang jelas asalnya. Pertahankan pembedaan antara tes dengan klien pengganti dan inferensi sebenarnya.
7. Periksa konflik revision, replay, respons hilang, pembacaan hasil setelah reload, RUNNING/UNKNOWN, serta pesan kegagalan. Frontend membaca keadaan backend sebelum retry dan tidak mengulang POST secara otomatis.
8. Verifikasi viewport dan perangkat/browser tujuan: menu, fokus error, formulir, pemilih bukti, tampilan hasil/peringatan, pemasangan PWA, dan pemberitahuan offline. Cache tetap hanya untuk aset UI, tanpa API, token, draft, bukti, atau hasil AI.

Contoh perintah dari root repository yang sudah digabung, pada PowerShell:

```powershell
cd code/backend
.\.venv\Scripts\Activate.ps1
python -m pip install --dry-run -r requirements-slr10.txt -r requirements-ai.txt
python manage.py check
python manage.py test accounts core reporting ai_pipeline.tests --settings=config.test_settings --verbosity=2
```

Perintah test di atas menggunakan konfigurasi PostgreSQL proyek. Mode SQLite komponen tetap hanya pelengkap pengujian terisolasi dan tidak mengganti database aplikasi. Jumlah tes setelah revisi dicatat dari hasil aktual.

Dari root repository, pemeriksaan frontend dan prototype:

```powershell
cd code/frontend
npm ci --ignore-scripts --no-audit --no-fund
npm test
npm run build
```

Setelah itu, kembali ke root repository untuk pemeriksaan prototype:

```powershell
cd ../..
node docs/uiux/tools/check.mjs
node docs/uiux/tools/review-check.mjs
node docs/uiux/tools/audit-check.mjs
```

Jika memakai terminal lain, pastikan tiga perintah `node docs/...` dijalankan dari root repository.

## 8. Dokumentasi dan paket revisi yang diserahkan

Perbarui bagian yang terdampak pada:

- `docs/slr10/README.md`, `API.md`, dan `INTEGRASI_SLR11.md`: daftar ekstensi/codec, recorder, kebutuhan decoder, serta dependensi gabungan.
- `docs/slr10/CHECKLIST_PENERIMAAN.md`: tandai hanya pekerjaan yang telah dibuktikan; pisahkan kesiapan implementasi dari penerimaan integrasi.
- `docs/slr10/HASIL_VERIFIKASI.md` dan `bukti-uji/`: catat lingkungan, versi kode/dependensi, perintah, jumlah tes, hasil aktual, serta keterbatasan.
- `tools/release-manifest.json`, bila installer dan ZIP distribusi tetap digunakan: regenerasi daftar/hash untuk berkas yang berubah dan build baru, dengan menjaga arti hash baseline yang dipakai mendeteksi konflik.
- Versi paket/build dan metadata penyerahan: gunakan versi revisi yang jelas. Build bawaan, source, lockfile, petunjuk, dan manifest installer harus merujuk versi yang sama.

Hasil yang diharapkan dari pelaksana SLR10:

1. Kode revisi atau commit yang dapat ditinjau, termasuk perubahan installer dan tes yang relevan.
2. Ringkasan berkas yang berubah serta penyelesaian setiap ID revisi.
3. Bukti pengujian ulang yang benar-benar dijalankan, dengan pembedaan komponen, PostgreSQL, browser, dan AI nyata.
4. Daftar bagian yang masih menunggu integrasi/review kelompok, berikut Commit SHA/URL setelah commit/push benar-benar dibuat.

`.env`, `.venv`, kredensial, media privat, dan bobot model tetap dikelola lokal. `.env.example` hanya berisi placeholder. Batas pekerjaan SLR10 tetap frontend, akun, draft, bukti/bundle, serta PWA; Human Verification, dashboard pengelolaan, dan Portal Publik mengikuti SLR12–SLR14.

## 9. Checklist penutupan revisi

- [ ] R10-01: format/codec, recorder, pesan UI, dan hasil unggah sesuai decoder SLR11.
- [ ] R10-02: dependensi gabungan dapat di-resolve; decoder gambar dan installer sudah diverifikasi.
- [ ] R10-03: harness prototype yang dibundel selesai dijalankan dengan LF/CRLF.
- [ ] R10-04: penyempurnaan peringatan NARA ditinjau bersama dan, bila diterapkan, lulus pemeriksaan tampilan tanpa mengubah flag/model.
- [ ] Regresi PostgreSQL 16 dan frontend dijalankan pada kode gabungan yang dicatat versinya.
- [ ] Alur aplikasi sampai hasil AI nyata diuji bersama dan bukti hasilnya tersedia.
- [ ] Pemeriksaan UI/UX/PWA pada browser/perangkat tujuan dicatat sesuai cakupan yang benar-benar diuji.
- [ ] Dokumentasi, build/manifest distribusi, dan Commit SHA/URL sesuai versi revisi.

Daftar ini menjadi dasar revisi dan review berikutnya. Tidak ada checkbox yang dianggap selesai hanya karena instruksinya sudah ditulis.
