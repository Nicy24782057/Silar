# Penghapusan laporan yang belum dikirim

Tambahan kontrak privat SLR14 yang diminta pada audit antarmuka. Kontrak publik
sembilan field dan kontrak tindakan SLR13 lainnya dipertahankan.

## Permintaan

`DELETE /api/v1/reports/{id}/`

- Bearer akun Reporter aktif, terverifikasi, dan pemilik laporan.
- `Content-Type: application/json`.
- `Idempotency-Key`: UUID baru untuk satu niat penghapusan. Simpan key dan isi
  yang sama bila respons hilang.

```json
{"expected_revision": 7}
```

Selain `expected_revision` tidak ada field lain yang diterima. Identitas pemilik
berasal dari akun terautentikasi dan database, bukan isian klien.

Respons berhasil, HTTP 200:

```json
{"data":{"id":"<uuid laporan>","revision":8,"deleted_at":"<waktu ISO 8601>"}}
```

## Batas dan hasil

Hanya laporan `NOT_SUBMITTED`, belum memiliki `submitted_at` atau versi resmi,
yang dapat dihapus. Analisis `RUNNING`/`UNKNOWN` menahan penghapusan sampai
keadaannya dipastikan. Laporan resmi tidak dapat dihapus oleh fitur ini.

Penghapusan bersifat logis: `deleted_at` dan `deleted_by` dicatat, revisi bertambah
satu, dan satu audit `REPORT_DELETED` disimpan dalam transaksi yang sama.
Laporan tidak muncul pada daftar/jumlah Reporter dan tidak dapat dilanjutkan.
Bukti, versi, narasi, hasil model, dan audit tetap tersimpan; fitur ini tidak
mengosongkan ruang media atau menyediakan pemulihan laporan.

Pembacaan rincian/versi/riwayat/bukti/media/run serta daftar/rincian request atas
laporan terhapus ditolak atau tidak ditampilkan. Pengecualian akses pemilik hanya
berlaku di DELETE untuk pemulihan respons dengan key/payload yang sama.

| Keadaan | HTTP / hasil |
| --- | --- |
| ID milik Reporter lain atau laporan tak dapat dibaca | 404 |
| Bukan Reporter aktif dan terverifikasi | 401/403 |
| Body/key tidak sah | 400 |
| Revisi sudah berubah | 409 `REVISION_CONFLICT` |
| Analisis masih berjalan/belum pasti | 409 `ANALYSIS_IN_PROGRESS` |
| Laporan sudah dikirim | 422 `TRANSITION_REJECTED` |
| Replay terminal identik selama masa replay masih berlaku | 200, `Idempotency-Replayed: true`; tidak menambah audit/revisi |
| Key/payload berbeda atau masa replay berakhir | 409; tidak menjalankan penghapusan baru |
| Audit gagal | Seluruh perubahan, revisi dan ledger dibatalkan |

Pemeriksaan akun/pemilik terbaru mendahului replay. Akun lain tidak dapat memakai
key pemilik. Respons yang hilang di UI menahan dialog dan menawarkan pemeriksaan
menggunakan DELETE identik; tidak ada retry otomatis. Respons HTTP yang sudah
pasti dapat ditutup, lalu daftar/detail dibaca ulang tanpa mengklaim keberhasilan.

## Migration dan verifikasi

`core/migrations/0005_report_soft_deletion.py` menambah kedua field, constraint
pemilik/status, dan trigger PostgreSQL `silar_deleted_report_guard`.
Trigger membuat keadaan terhapus terminal dan menjaga seluruh sumber saat
penghapusan. Migration tidak menghapus baris/media dan mempertahankan guard lama.

Sebelas tes komponen mencakup kepemilikan, status resmi, analisis berjalan,
revisi, replay/expiry, kebocoran pembacaan, input, constraint dan rollback audit.
Tiga tes PostgreSQL disiapkan untuk DELETE bersamaan, DELETE melawan submit, dan
larangan perubahan/pemulihan melalui SQL. Tes PostgreSQL belum berjalan di
lingkungan ini; jalankan perintah pada [UJI_POSTGRESQL16.md](UJI_POSTGRESQL16.md).
