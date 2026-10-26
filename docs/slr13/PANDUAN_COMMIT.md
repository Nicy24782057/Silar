# SLR_13 — Panduan commit dan pencatatan bukti

Jalankan dari terminal PowerShell di folder proyek setelah patch Operator/Admin, Update 02 dan Update 03 berhasil dipasang serta dokumentasi ini disalin.

## 1. Periksa perubahan dan branch

```powershell
git status --short
git branch --show-current
git diff --stat
```

Gunakan branch kerja kelompok yang disepakati. Cocokkan perubahan dengan implementasi yang hendak dicatat.

## 2. Stage berkas yang terkait SLR_13

Daftar berikut mencakup berkas patch awal dan kedua pembaruan. Berkas yang sudah sama dengan commit sebelumnya tidak akan menjadi perubahan baru.

```powershell
$silar13Files = @(
    "code/backend/accounts/serializers.py"
    "code/backend/accounts/services.py"
    "code/backend/config/urls.py"
    "code/backend/core/audit.py"
    "code/backend/reporting/workspace_services.py"
    "code/backend/reporting/workspace_urls.py"
    "code/backend/reporting/workspace_views.py"
    "code/backend/reporting/tests/test_workspace.py"
    "code/backend/reporting/tests/test_workspace_update02.py"
    "code/backend/reporting/tests/test_workspace_update03.py"
    "code/frontend/src/App.vue"
    "code/frontend/src/components/AppIcon.vue"
    "code/frontend/src/components/WorkspaceAssignment.vue"
    "code/frontend/src/components/WorkspaceEvidence.vue"
    "code/frontend/src/components/WorkspaceStatus.vue"
    "code/frontend/src/main.js"
    "code/frontend/src/router.js"
    "code/frontend/src/views/AuthView.vue"
    "code/frontend/src/views/NotificationsView.vue"
    "code/frontend/src/views/WorkspaceView.vue"
    "code/frontend/src/views/WorkspaceAuditView.vue"
    "code/frontend/src/views/WorkspaceOperatorsView.vue"
    "code/frontend/src/views/WorkspaceReportView.vue"
    "code/frontend/src/views/WorkspaceReportsView.vue"
    "code/frontend/src/views/WorkspaceServicesView.vue"
    "code/frontend/src/workspace.css"
    "code/frontend/src/workspace.js"
    "code/frontend/tests/workspace.test.js"
    "code/frontend/tests/workspace-update02.test.js"
    "code/frontend/tests/workspace-update03.test.js"
    "docs/slr13"
)
git add -- $silar13Files
```

Jika suatu path belum ada, hentikan langkah commit dan periksa pemasangan paket yang sesuai. Folder build produksi mengikuti kebijakan repositori yang sudah mengabaikan code/frontend/dist; source frontend dan tes tetap dicatat.

## 3. Tinjau yang akan masuk commit

```powershell
git diff --cached --name-only
git diff --cached --stat
git diff --cached
```

Pastikan isi staged sesuai pekerjaan SLR_13. Bila sebelumnya sudah ada perubahan lain dalam staging area, periksa agar tidak ikut masuk tanpa sengaja. Daftar di atas hanya memilih source, tes dan dokumentasi yang terkait.

## 4. Buat commit lokal dan ambil SHA

```powershell
git commit -m "SLR_13_Implementasi dan verifikasi workspace Operator dan Admin"
git log -1 --format="%H"
```

Commit hanya mencatat perubahan lokal. Pengiriman commit ke remote mengikuti branch dan prosedur kelompok yang sudah disepakati.

## 5. Catat pada card SLR_13

- Salin SHA lengkap dari keluaran git log.
- Setelah commit tersedia pada remote kelompok, buka halaman commit dan salin URL sebenarnya.
- Cantumkan SHA/URL tersebut di bagian Bukti Pekerjaan pada card SLR_13.
- Tinjau dokumentasi dan bukti; poin dokumentasi/commit dapat dicentang setelah keduanya lengkap.
- Poin pengujian terintegrasi tetap menunggu SLR_14/SLR_15.

Status sebelum langkah-langkah ini dijalankan: commit kelompok belum dibuat oleh paket dokumentasi ini; SHA/URL belum dicatat.

