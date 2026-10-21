# Bukti Review SLR_07

| Berkas | Lingkup bukti |
| --- | --- |
| hasil-pemeriksaan-teknis.json | Eksekusi terbaru 15 uji tambahan pada paket hasil perbaikan; ID RT-01–RT-15, waktu, versi Node dan hash aset. |
| hasil-regresi-audit.json | Eksekusi terbaru 3 regresi menu/kontras; handler klik dan perhitungan sRGB, bukan browser. |
| regresi-audit-sebelum-2026-10-18.json | Tiga regresi gagal sebelum perbaikan; disimpan sebagai riwayat. |
| hasil-pemeriksaan-teknis-2026-10-16.json | Hasil teknis paket awal, tidak ditimpa oleh hasil terbaru. |
| audit-sumber-2026-10-18.md | Salinan laporan audit yang dikirim pengguna. Mencakup 07/08; tindak lanjut paket ini berada pada SLR_07. |

Hasil browser dalam sumber audit berlaku pada paket awal dengan SHA-256 yang dicatat. Auditor memakai Linux/Chromium dan viewport simulasi; bukti tersebut bukan hasil fisik Android/Windows atau pemeriksaan visual ulang paket terbaru. Nama auditor dan penerimaan kelompok tidak disebut dalam laporan sumber.

Review pengguna awal: Nicy Putra Pratama, 16 Oktober 2026. Screenshot/rekaman manual dan catatan penerimaan kelompok belum dilampirkan pada sumber yang diterima. Tambahkan bukti nyata di folder ini, misalnya U07-16-menu-draft-lama-390.png dan U07-16-menu-draft-baru-360.png. Catat lingkungan, hasil dan tautannya pada review-results.md. Gunakan data fiktif.

Untuk menyimpan hasil eksekusi teknis baru tanpa menghapus bukti sebelumnya:

```sh
node docs/uiux/tools/review-check.mjs --report docs/uiux/bukti-review/hasil-pemeriksaan-teknis-ulang.json
node docs/uiux/tools/audit-check.mjs --report docs/uiux/bukti-review/hasil-regresi-audit-ulang.json
```
