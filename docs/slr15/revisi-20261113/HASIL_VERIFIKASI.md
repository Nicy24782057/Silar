# Hasil verifikasi revisi akun, Operator dan setup

Dilakukan pada 12 November 2026 UTC / 13 November 2026 WIB, terhadap perubahan lokal di atas main `7af81c8e448e12eead2b54a4e6aad72b9e2a781e`. Tidak ada commit, push, deployment, atau perubahan status board pada pekerjaan ini.

Lingkungan: Linux, Python 3.12.14, PostgreSQL 16.14, Django 5.2.18, Node.js 24.22.1. Pengujian backend memakai PostgreSQL asli pada database uji terpisah. Pemeriksaan identitas proses, trigger dan constraint tidak dilewati.

| Pemeriksaan | Hasil | Bukti |
| --- | --- | --- |
| Verifier SLR14, termasuk integrasi pipeline | 152 lulus; 0 gagal/error/skip | [JSON](bukti/native-152.json), [log](bukti/native-152.txt) |
| Akun lama dan alur akun tambahan | 51 lulus | [Log akun](bukti/account-tests.txt) |
| Orkestrasi setup dan pemeriksaan kesiapan | 25 lulus | [Log setup](bukti/setup-tests.txt) |
| Unit frontend | 111 lulus; 0 gagal/skip | [Log frontend](bukti/frontend-tests.txt) |
| Build frontend | Berhasil | [Log build](bukti/frontend-build.txt) |
| Konsistensi model dan migration | `No changes detected` | [Log migration](bukti/migration-check.txt) |
| Django system check | Tidak ada masalah | [Log check](bukti/django-check.txt) |
| Browser, reduced motion | 91 keadaan tampilan, 3 alur; tanpa page error | [Hasil browser](bukti/browser-result.json) |
| Browser, animasi aktif | 11 keadaan tampilan, 3 alur; tanpa page error | [Hasil animasi](bukti/browser-motion-result.json) |

Angka pada tabel adalah kelompok pengujian terpisah, bukan satu perintah tes gabungan. Verifier SLR14 tidak menggantikan kelompok tes akun tambahan.

## Cakupan akun dan keamanan alur

Tes memeriksa verifikasi Reporter tanpa tautan, undangan Operator dengan bukti aktivasi sekali pakai, akun tetap nonaktif sebelum sandi tersimpan, penolakan sandi lemah, kedaluwarsa dan pemalsuan bukti, pencabutan setelah kirim ulang, serta penolakan pemilihan peran dari payload publik. Pembatasan pemeriksaan diuji lintas IP, kirim ulang, dan endpoint lama. Permintaan bersamaan hanya boleh menghasilkan satu keberhasilan untuk kode dan bukti aktivasi yang sama. Kode, bukti dan sandi diperiksa tidak masuk audit.

Pola sandi yang diuji mencakup identitas ditambah angka/simbol, variasi sederhana dengan penggantian huruf/angka, pengulangan dan urutan keyboard. Frasa yang memenuhi aturan tetap diterima tanpa kewajiban campuran jenis karakter. Pemeriksaan ini tidak mencakup seluruh kemungkinan sandi lemah atau database sandi bocor.

## Cakupan browser

Chromium headless menjalankan frontend Vue dan backend Django yang sebenarnya, dengan email berkas lokal. Matriks utama memakai lebar 1440, 1100, 820, 640, 390 dan 320 piksel dalam mode terang/gelap. Diperiksa overflow horizontal, keberadaan kedua panel hanya pada desktop/tablet, kolom kode yang dapat diisi, tiga tahap Operator, dialog riwayat, laporan terbit/ditutup/tidak valid, dan tidak tampilnya sumber privat pada Admin monitoring. Angka 91 berarti keadaan yang diperiksa otomatis; bukan 91 tangkapan layar yang dibandingkan dengan desain sumber.

Tiga alur yang berhasil dijalankan melalui antarmuka:

1. Registrasi Reporter → email terisi di formulir kode → kode salah ditolak → kode benar → tombol login, tanpa membuka tautan email.
2. Satu tautan Verifikasi akun → kode Operator → sandi lemah ditolak → sandi yang memenuhi aturan → akun aktif.
3. Simpan review → keadaan tersimpan dibaca kembali → otomatis ke Tindak lanjut → lewati catatan opsional → Keputusan → pratinjau/konfirmasi → tindakan publikasi eksplisit.

Alur tersebut juga dijalankan dengan preferensi animasi normal. Pemeriksaan ini membuktikan alur tetap berfungsi selama transisi; bukan pengukuran frame rate pada setiap perangkat. Pratinjau bukti dan rincian AI juga dibuka. Penyimpanan browser diperiksa tidak memuat sandi uji.

Tangkapan layar berikut diperiksa secara visual untuk keterbacaan dan tumpang tindih:

- [Pemeriksaan Operator desktop terang](bukti/operator-inspection-1440-light.png).
- [Pemeriksaan Operator ponsel gelap](bukti/operator-inspection-390-dark.png).
- [Verifikasi akun ponsel terang](bukti/verify-email-390-light.png).
- [Registrasi desktop gelap](bukti/register-1440-dark.png).

ZIP desain asli tidak tersedia pada workspace pemeriksaan ini. Karena itu hasil ini tidak menyatakan perbandingan piksel terhadap seluruh desain asli.

## Batas hasil

- Sembilan tes integrasi pipeline memakai klien model/provider simulasi. Decoder, API, penyimpanan dan izin dijalankan nyata; inferensi SENA/NARA/Whisper/Gemini asli tidak dijalankan dalam revisi ini.
- Tidak ada email eksternal yang dikirim. Pengiriman SMTP ke Gmail harus diuji sesudah konfigurasi pengirim tersedia pada lingkungan pemilik.
- Pengujian setup mencakup pemilihan langkah, kegagalan, versi venv, paket/impor dan decoder melalui tes terisolasi. Instalasi Windows baru beserta unduhan seluruh paket AI/bobot model belum dijalankan di sini.
- Uji browser memakai desktop Chromium emulasi ukuran layar. Safari/iOS dan perangkat fisik tidak diuji dalam revisi ini.

## Mengulang pemeriksaan utama

Dari `code/backend`, gunakan venv aplikasi yang lengkap dan PostgreSQL 16 dengan izin membuat database uji:

```powershell
.\.venv\Scripts\python.exe verify_slr14.py --include-pipeline-integration
.\.venv\Scripts\python.exe manage.py test accounts.tests accounts.test_account_flow --settings=config.test_settings --verbosity=2
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py check
```

Dari folder utama, dengan Python 3.12 dan dependensi backend tersedia:

```powershell
py -3.12 -m unittest tools.tests.test_setup_silar tools.tests.test_install_slr10
```

Dari `code/frontend`, jalankan `npm.cmd test` dan `npm.cmd run build`.

Manifest SHA-256 pada `DAFTAR_PERUBAHAN.json` mengidentifikasi berkas revisi dan bukti yang disertakan. Kredensial, email mentah, fixture rahasia, database serta bobot model tidak termasuk bukti.
