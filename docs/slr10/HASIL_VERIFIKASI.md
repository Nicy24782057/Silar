# Hasil verifikasi SLR_10 revisi 1.1.0

Tanggal: 22 Oktober 2026. Lingkungan penyusun: Linux, Python 3.12.14, Node.js 24.19.0, Pillow 13.0.0, Vue 3.5.44/Vite 7.3.7, FFmpeg 6.1.1 dan Chromium 140.0.7339.16. Source dan lockfile mengikuti versi 1.1.0. Bukti 1.0.0 dipisahkan dalam bukti-uji/historis-v1.0.0.

| Pemeriksaan | Hasil aktual | Batas bukti |
| --- | --- | --- |
| Backend reporting | 39 tes lulus | Django API/ORM dan decoder aktual dengan SQLite terisolasi; tidak membuktikan trigger/lock PostgreSQL. |
| Frontend/PWA | 24 tes lulus | Validasi kanal/batas, pilihan recorder, identitas hasil/peringatan dan kebijakan cache. |
| Build produksi | Berhasil, 44 modul | Build Vue tersaji melalui proxy Python; source/build adalah versi revisi. |
| Browser | 28 skenario lulus | Login/input menggunakan HTTP Django aktual. Empat skenario hasil NARA memakai respons sintetis; dua fallback recorder memakai kegagalan kemampuan/izin yang disimulasikan. |
| Prototype LF | 42 + 15 + 3 lulus | Harness VM/proyeksi HTML SLR_07; berbeda dari browser Vue. |
| Prototype CRLF | 42 + 15 + 3 lulus | Akhir baris diubah pada salinan sementara; sumber desain tidak diganti. |
| Unit pemasang | 11 tes lulus | Upgrade pin/sumber, preflight, backup, idempotensi, CRLF, sumber tampered dan preservasi pada repository sintetis. |
| Pemasangan paket lengkap | 6 skenario lulus | Salinan SLR_08, upgrade payload v1.0.0 sebenarnya, reinstall, CRLF versi baru, konflik lokal dan konfigurasi origin; file AI berupa sentinel preservasi. |
| Sintaks dan fondasi | 61 berkas Python dapat diparse; Django check lulus; accounts/common/core identik byte terhadap paket sebelumnya | Tidak menggantikan pengujian SQL/migrasi PostgreSQL. |
| Dependensi SLR_10 | Instalasi Pillow 13.0.0 dan pip check lulus | Requirements lengkap SLR_11 belum tersedia; resolver gabungan AI belum dinyatakan lulus. |
| Windows/PostgreSQL 16 | Belum dijalankan untuk revisi ini | Jalankan pada konfigurasi tim, termasuk port 5433 yang sudah berhasil. |
| Loader/pipeline SLR_11 nyata | Belum dijalankan | Tidak ada kode/aset AI lengkap pada lingkungan penyusun revisi. |

## Media yang benar-benar diuji

Audio sintetis pendek dibuat dengan codec sesungguhnya dan didekode oleh FFprobe/FFmpeg. WAV PCM, MP3, WebM/Opus, M4A/AAC dan MP4/AAC diterima melalui decoder dan API; byte asli, hash serta akses privat diperiksa. OGG/Opus, M4A/ALAC, WebM/Vorbis, WAV/ADPCM, MP4/video serta MP3/cover gambar ditolak. Ekstensi palsu, MIME salah, kerusakan, ukuran di atas batas, dan durasi 121 detik ditolak. Decoder yang hilang menghasilkan kegagalan layanan yang berbeda dari berkas tidak valid.

PNG/JPEG diverifikasi dan didekode memakai Pillow 13.0.0; ketidaksesuaian ekstensi/MIME dan dimensi berlebih tetap ditolak. Hasil ini bukan pengujian Whisper atau akurasi model.

## Browser dan pembacaan hasil

Alur akun, draft, upload, bukti sebelum bundle, media privat dan bundle diperiksa lewat Vue produksi dengan backend HTTP aktual. MediaRecorder memakai mikrofon sintetis Chromium, menghasilkan WebM/Opus dan berhasil diunggah. Pemilih berkas MP4/AAC serta penolakan OGG diperiksa. Viewport 360/390/768/1366 tidak mengalami overflow horizontal; menu ponsel menutup setelah navigasi. Cache/storage dan navigasi offline tetap dibatasi ke antarmuka.

Peringatan NARA diuji secara eksplisit dengan fixture JSON sintetis: uncertain false dengan peringatan; uncertain true dengan peringatan; daftar peringatan kosong; serta run terbaru FAILED/NARA kosong dengan kartu lama. Pemeriksaan tampilan desktop/ponsel dilakukan pada screenshot internal. Tidak ada fixture yang ditambahkan sebagai hasil AI contoh pada aplikasi yang diserahkan. Tidak ditemukan exception JavaScript pada 28 skenario tersebut.

## Pengujian yang masih harus dilakukan kelompok

1. Pasang revisi dan jalankan SIAPKAN_SLR10.bat pada repository gabungan. Jika requirements-ai.txt ada, setup menggunakan satu resolver untuk kedua berkas.
2. Jalankan UJI_SLR10.bat. Bagian Django memakai config.test_settings dan PostgreSQL dari .env asli; bagian frontend membutuhkan Node/npm. Catat jumlah/hasil aktual.
3. Uji lima format audio melalui API SLR_10 hingga ai_pipeline.sources.load_sources. Konfirmasikan kebijakan cover/stream video terhadap decoder SLR_11 aktual.
4. Jalankan tujuh rute dengan aset model/API nyata, lalu uji revision, replay, respons hilang, RUNNING/UNKNOWN dan reload. Pisahkan fixture dari inferensi nyata.
5. Periksa perangkat Windows/Android, instalasi PWA dan keyboard/fokus; catat review dan Commit SHA/URL setelah dilakukan.

Tidak ada klaim kelulusan AI, PostgreSQL atau perangkat fisik berdasarkan fixture. Setup dan halaman login Windows v1.0.0 yang dilaporkan pemilik proyek merupakan bukti historis terpisah, bukan penerimaan revisi ini.
