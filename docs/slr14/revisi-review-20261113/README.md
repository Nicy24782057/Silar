# SLR14 — revisi hasil review, 13 November 2026

Perubahan implementasi tetap berada dalam SLR14. SLR15 menjadi kegiatan pengujian dan pencatatan temuan. Revisi ini melanjutkan paket `SILAR_SLR15.zip` yang sudah diterapkan; bukan pengganti seluruh repository. Bukti paket akun/Operator sebelumnya tetap disimpan sebagai riwayat di `docs/slr15/revisi-20261113/`.

## Perubahan

- Kolom sandi utama dan konfirmasi menggunakan komponen `PasswordInput.vue` yang sama. Ikon mata berada di dalam ujung kanan kolom dengan area tekan 44 × 44 piksel dan ruang teks tersendiri. Lebar kolom sama dengan kolom email.
- Setiap kolom memiliki keadaan terlihat/tersembunyi sendiri. Tombol memiliki nama aksesibel, petunjuk, keadaan `aria-pressed` dan fokus keyboard. Menekannya tidak mengirim formulir. Kolom kembali tersembunyi saat dikosongkan atau dinonaktifkan selama pengiriman.
- Kontrol dipakai pada login, registrasi Reporter, aktivasi Operator dan reset sandi. Label, petunjuk panjang minimum dan atribut password manager tetap diteruskan ke input asli.
- Tombol Masuk pada navigasi dan hero mengikuti latar halaman dengan garis tipis. Tombol Buat akun memakai gradasi aksen biru–sian dan bayangan halus. Mode terang/gelap serta fokus/hover memiliki warna yang sesuai. Tombol tema juga mengikuti latar navigasi.
- Catatan utama menempatkan implementasi pada SLR14, memperbarui petunjuk Pemeriksaan Operator dan menjelaskan command penyiapan SENA/NARA serta Whisper. Perubahan ini tidak menambah dependensi atau migration backend.

## Hasil verifikasi revisi ini

| Pemeriksaan | Hasil |
| --- | --- |
| Tes frontend | 111 lulus, 0 gagal/skip; [log](bukti/frontend-tests.txt) |
| Build produksi | Berhasil; [log](bukti/frontend-build.txt) |
| Browser dengan animasi aktif | 72 keadaan halaman/ukuran/tema, tanpa overflow horizontal |
| Kontrol sandi | 86 pemeriksaan toggle, keyboard, ukuran, posisi, jarak teks dan kemandirian kolom |
| Alur akun melalui UI | 3 alur berhasil, 0 page error; [hasil JSON](bukti/browser-result.json) |

Browser Chromium headless memeriksa lebar 1440, 1100, 820, 640, 390 dan 320 piksel dalam mode terang/gelap. Matriks mencakup landing page, Portal Publik, login, registrasi, reset dan pembuatan sandi Operator. Backend Django berjalan pada PostgreSQL uji terpisah; email ditulis ke berkas lokal.

Tiga alur yang berhasil:

1. Registrasi Reporter, kontrol sandi terpisah, tombol dinonaktifkan dan sandi disembunyikan selama pengiriman, lalu verifikasi kode.
2. Permintaan email pemulihan lokal, reset sandi melalui challenge asli, penyimpanan sandi baru, kemudian login/logout Reporter.
3. Verifikasi kode Operator, kontrol sandi/konfirmasi pada 12 kombinasi ukuran/tema, lalu aktivasi sebenarnya.

Tautan Masuk di navigasi dan Buat akun di hero juga diperiksa menuju formulir yang benar. Sandi uji tidak disimpan pada localStorage/sessionStorage. Tampilan desktop dan ponsel diperiksa secara visual pada tangkapan layar internal; gambar tersebut tidak disertakan sebagai berkas paket.

Kelompok backend 152 tes SLR14, 51 tes akun dan 25 tes setup dari paket sebelumnya tidak dijalankan ulang untuk perubahan UI ini. Tidak ada inferensi AI asli atau pengiriman SMTP eksternal dalam verifikasi revisi ini. Pemeriksaan tidak menyatakan penerimaan SLR15, pengujian perangkat fisik, atau kesamaan piksel terhadap ZIP desain asli yang tidak tersedia pada workspace.

## Memasang paket lanjutan

1. Terapkan paket akun/Operator/setup sebelumnya terlebih dahulu. Migration akun `0002_emailotp_activation_auth_version_and_more` harus sudah diterapkan.
2. Hentikan server dan gabungkan berkas dari ZIP lanjutan mengikuti path. Jangan mengganti seluruh folder repository. Konfigurasi, database dan model lokal tetap digunakan.
3. Dari `code/frontend`, jalankan `npm.cmd test`, `npm.cmd run build`, kemudian `npm.cmd run dev`. Mulai ulang backend. Perbarui build pada PWA yang terpasang.

Alternatif penyalinan berkas adalah `git apply --check PERUBAHAN_SLR14_UI.patch`, lalu `git apply PERUBAHAN_SLR14_UI.patch` dari root clone. Patch dibuat terhadap isi source paket akun sebelumnya dan versi awal dokumen SLR14 pada commit `7af81c8e448e12eead2b54a4e6aad72b9e2a781e`. Jika berkas tersebut sudah diedit lagi, periksa perbedaannya sebelum menggabungkan. Pilih penyalinan berkas atau patch; tidak perlu melakukan keduanya.

Manifest SHA-256 terdapat pada `DAFTAR_PERUBAHAN.json`. Manifest lama di folder bukti SLR15 tetap merekam isi paket lama, bukan versi source sesudah revisi UI ini.

## Pemeriksaan AI pada komputer pemilik

Ukuran arsip yang dilaporkan pemilik sesuai metadata proyek: SENA 412.184.854 byte dan NARA 408.238.634 byte. Ukuran cocok menunjukkan arsip bukan penunjuk Git LFS kecil, tetapi belum menggantikan verifikasi hash atau membuktikan model siap dimuat.

Dari `code/backend`, jalankan `manage.py prepare_ai_models` memakai Python venv backend. Command memverifikasi hash dan menyiapkan hasil ekstraksi yang dibaca runtime. Mulai ulang backend dan coba teks terlebih dahulu. Audio memerlukan Whisper dan foto/kombinasi memerlukan konfigurasi Gemini; prosedur ada di `PANDUAN_RUNNING.md`. Runtime saat ini memakai CPU, tanpa kewajiban NVIDIA/CUDA. Hasil command maupun inferensi pada komputer pemilik belum diterima dalam pekerjaan ini.

## Tindak lanjut

Perubahan alur sesi masih memerlukan identifikasi ikon silang yang dimaksud pengguna. Menutup menu, menutup tab/aplikasi dan Keluar akun adalah tindakan berbeda; revisi UI ini mempertahankan perilaku sesi yang ada.

Tidak ada commit, push, deployment atau perubahan board oleh penyusun. Setelah review, nama commit lanjutan yang sesuai adalah `fix(slr14): rapikan ikon sandi dan tombol landing page`.
