# Penempatan dan penyerahan kelompok

Paket disusun sebagai tambahan `code/backend` dan `docs/backend`. Folder UI/UX SLR_07 tetap `docs/uiux`. Uji lebih dahulu dari hasil ekstraksi sementara. Jika repository telah berisi backend atau migration tim, bandingkan perubahan sebelum menggabungkan; jangan menimpa sumber tanpa review atau mengarahkan migration baru ke database lama tanpa pemetaan.

Setelah lokal berjalan, dari akar repository SILAR buat branch pekerjaan dengan nama yang disepakati, misalnya `feature/slr-08-backend`. Salin kedua folder pada jalur yang sama. `.gitignore` backend sudah mengecualikan `.env`, virtual environment, email lokal, media dan aset model. Tinjau `git status` dan daftar berkas yang akan di-commit untuk memastikan tidak ada kredensial, data email atau database.

```bat
git switch -c feature/slr-08-backend
git add code/backend docs/backend
git diff --cached --stat
git status
```

Setelah peninjauan tim, commit/push mengikuti alur repository kelompok. Dokumen ini tidak menyatakan commit atau push telah dilakukan. `baseline.json` mencatat commit **sumber acuan**; nilai tersebut bukan commit pekerjaan backend baru.

## Keterlacakan card

| Kebutuhan SLR_08 | Bukti lokal |
| --- | --- |
| Django/DRF/PostgreSQL/environment/versi | requirements, settings, setup, hasil verifikasi |
| Custom User UUID sebelum migration | accounts/models.py dan accounts/0001_initial |
| Model, FK/pointer siklik, constraint, indeks | core/models.py, core/migrations, database-dan-layanan.md |
| Migration dan integritas RUNNING/UNKNOWN | log migration, core/tests.py |
| FR01, AC-F01 | accounts/services.py, views.py, serializers.py dan accounts/tests.py |
| JWT, cookie, CSRF, revoke | authentication.py, services, AuthAPIView dan test |
| NFR01, AC-N01 | core/permissions.py, JWT live user, test ownership/grant/assignment/replay |
| Storage/aset privat | core/storage.py dan konfigurasi folder privat |
| Validasi/error/revision/idempotency | common/api.py, core/mutations.py, tests |
| FR23, AC-F23 | core/audit.py, model/trigger audit, GET admin/audit dan tests |
| Dokumentasi dan handoff | README, frontend-handoff, OpenAPI dan hasil-verifikasi |
| Bukti commit dan penerimaan kelompok | **Belum diisi**; dilengkapi setelah tindakan aktual |

Pengujian ini merupakan bukti fondasi, bukan penerimaan terintegrasi seluruh FR pendukung. Antarmuka akun berada pada SLR_10, pengelolaan Operator pada SLR_13, dan audit setiap fitur ditambahkan pemilik layanan terkait. Penerimaan lintas card mengikuti SLR_15.

## Catatan review yang diisi tim

| Item | Nilai |
| --- | --- |
| Reviewer/tanggal | Belum diisi |
| OS/Python/PostgreSQL/browser/origin | Belum diisi |
| Temuan, tindakan dan bukti perubahan | Belum diisi |
| URL repository/PR | Belum diisi |
| Commit SHA pekerjaan SLR_08 | Belum diisi |
| Penerimaan kelompok | Belum diisi |

Tambahkan bukti manual yang sudah dibersihkan dari password, OTP, token, isi email dan data pribadi pada `docs/backend/bukti-review/`. Pertahankan kode dan dokumentasi yang dapat diedit. Tidak ada klaim review atas nama anggota kelompok pada hasil paket ini.
