# Revisi SLR14 — kewenangan Operator lengkap

Paket perubahan berdasarkan GitHub main yang diperiksa pada commit
`785a2762a9f7dcbd8ecfb1522165995e6c02b0cd` (`SLR_15 Mutu AI`). Ini revisi SLR14, belum dipush atau diterapkan
ke server. Akun Operator baru dan lama yang aktif/terverifikasi memperoleh
ketujuh kewenangan penanganan. Admin cukup mengisi nama dan email. Batas
penugasan dan aturan keamanan/penutupan/publikasi tetap diperiksa.

## Memasang

1. Ekstrak ZIP ke folder sementara. Pertahankan perubahan lokal tim.
2. Periksa kecocokan patch dari folder utama repository:

   ```powershell
   git status --short
   git apply --check "C:\lokasi\paket\PERUBAHAN_OPERATOR.patch"
   ```

3. Jika pemeriksaan berhasil, terapkan **satu kali**:

   ```powershell
   git apply "C:\lokasi\paket\PERUBAHAN_OPERATOR.patch"
   ```

   Alternatifnya, gabungkan hanya berkas `code/`, `docs/` dan
   `PANDUAN_RUNNING.md` dalam ZIP sesuai path aslinya. Pilih salah satu cara;
   jangan menerapkan patch lalu menyalin ulang perubahan yang sama.

   Jika teman sudah mengubah berkas yang sama dan patch ditolak, gabungkan
   bagian perbedaannya terlebih dahulu. Jangan memaksa penimpaan perubahan tim.
4. Perbarui frontend dan backend bersamaan, lalu mulai ulang keduanya. Tidak
   ada dependensi/migration baru; tidak perlu mengatur izin ulang setiap akun.
5. Jalankan pemeriksaan pada `docs/slr14/revisi-izin-operator-20261116/HASIL_UJI.md`
   dan lakukan review manual sesuai README dalam folder tersebut.

`permission_ids` tidak lagi diterima dalam POST/PATCH Operator. Field pada
respons tetap ada sebagai metadata baca saja. Frontend lama perlu diperbarui.

## Ringkasan uji

268 tes backend PostgreSQL 16 dan 123 tes frontend lulus. Build, pemeriksaan
Django, schema dan 10 kombinasi ukuran/tema serta 7 alur browser lulus.
Pengujian memakai akun/data uji dan kotak email lokal, tanpa inferensi AI nyata
atau deployment server. Hasil lengkap dan batas verifikasi ada dalam dokumen.

Saran judul commit:

```text
SLR_14 Menyederhanakan kewenangan Operator menjadi paket lengkap
```

ZIP berisi berkas yang berubah, kontrak/dokumentasi, patch dan checksum.
Konfigurasi rahasia, database, model AI, dependency, build dan tangkapan layar
tidak disertakan. Panduan menjalankan seluruh proyek tetap mengikuti
`PANDUAN_RUNNING.md`.
