# Finalisasi Review Setelah Audit SLR_07

Diperbarui 18 Oktober 2026. Audit sumber telah membuktikan tujuh alur browser pada paket awal, termasuk login/OTP serta jalur Operator sampai close. Menu/avatar telah diperbaiki dan 60 pemeriksaan teknis lulus pada sumber terbaru. Langkah berikut adalah pengujian yang masih perlu bukti aktual; bukan pernyataan bahwa kegiatan sudah dilakukan.

## Membuka paket

Ekstrak ZIP, salin folder docs ke akar SILAR, lalu jalankan `py -m http.server 8000 --directory docs/uiux/prototype`. Gunakan python/python3 bila py tidak tersedia. Buka http://localhost:8000 dan muat ulang penuh sebelum alur baru. Akun fixture Reporter: pelapor@contoh.test / Silar123!; OTP 123456. Mulai ulang/refresh mereset data contoh.

## A07-01 — Uji ulang menu

| Kasus | Langkah | Hasil yang diperiksa |
| --- | --- | --- |
| Draft sudah ada | Lebar 390 px → Reporter → buka menu → Buat Laporan. | RP02 terbuka, menu/overlay hilang dan textarea serta tindakan formulir dapat digunakan. |
| Draft baru | Mulai ulang → selesaikan draft contoh sampai konfirmasi dan submit → buka menu → Buat Laporan. | Satu draft baru terbuka dan menu/overlay hilang. |
| Tidak menggandakan draft | Dari draft baru, buka menu lalu pilih Buat Laporan kembali. | Draft yang sama dibuka; jumlah draft tidak bertambah. |
| Ukuran sempit | Ulangi kasus draft lama dan baru pada lebar 360 px. | Formulir langsung dapat digunakan tanpa menutup overlay secara manual. |
| Pergantian ukuran | Sesudah navigasi Buat Laporan, beralih antara 390 px dan 1366 px, lalu kembali; buka/tutup menu kembali pada ponsel. | Tujuan/formulir tetap sesuai, tidak ada overlay tertinggal, menu masih dapat dibuka/ditutup. |

Jika memakai emulasi browser, catat sebagai simulasi viewport. Bukti pada perangkat nyata dicatat terpisah. Simpan screenshot/rekaman relevan dan kaitkan dengan A07-01 serta U07-16.

## A07-02 — Avatar

Periksa avatar pada sidebar desktop. Warna teks telah dibuat eksplisit #1d2b32 pada #edf1f2; perhitungan sRGB 12,79:1. Ulangi pemeriksaan kontras melalui browser/alat yang dipakai kelompok, catat hasil serta versinya. Jangan menyimpulkan seluruh UI memenuhi aksesibilitas hanya dari avatar atau pemindaian otomatis.

## A07-03 — Review perangkat dan penerimaan kelompok

1. Catat nama reviewer, tanggal, perangkat/OS/browser/versi, viewport serta identitas paket atau commit yang benar-benar dipakai.
2. Periksa alur utama Reporter/Publik pada sasaran Android Chrome dan Operator/Admin pada Windows Chrome/Edge. Bedakan perangkat nyata dari emulasi viewport.
3. Periksa menu, keyboard, dialog, fokus, pesan error dan pemahaman batas AI/privasi. Catat titik bingung dan tindak lanjut yang diamati.
4. Gunakan test-plan.md sebagai acuan cakupan. Hasil browser auditor dan uji teknis yang sudah tersedia dapat menjadi bahan review; tidak perlu mengulang pekerjaan dari awal tanpa alasan.
5. Isi keputusan kelompok di review-results.md: diterima untuk lingkup SLR_07, atau perlu perbaikan dengan alasan/tindak lanjut. Jangan mengisi keputusan sebelum kelompok menetapkannya.
6. Jika review sudah dilakukan di luar ZIP, cukup lampirkan/tautkan catatan aktual. Setelah kelompok commit/push, tautkan commit final ke card.

## Ringkasan yang perlu dikirim untuk memperbarui hasil

- Nama reviewer dan tanggal review akhir.
- Perangkat, OS, browser/versi, viewport; nyata atau simulasi.
- Hasil uji ulang menu lama/baru, perubahan ukuran dan avatar.
- Temuan/usability serta tindak lanjut bila ada.
- Keputusan penerimaan kelompok dan tautan bukti/commit bila sudah tersedia.

Laporan audit sumber tidak menyebut nama personal auditor atau keputusan kelompok. Nama penguji awal Nicy Putra Pratama tidak otomatis menjadi reviewer akhir. Status tetap In Review sampai bukti penutupan tersedia sesuai lingkup perancangan/prototype.
