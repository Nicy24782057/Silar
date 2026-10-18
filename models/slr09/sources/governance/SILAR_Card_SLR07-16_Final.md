# Teks Card SLR_07–SLR_16 — Pemetaan Final SILAR

Setiap bagian dimulai dari judul card dan dapat disalin sebagai teks pengganti pada GitHub Project. Nomor serta judul tahapan tetap mengikuti rencana proyek. Semua task belum dicentang; bukti implementasi diisi ketika pekerjaan tersedia.

## Acuan

- PRD SILAR versi **0.5**: `docs/product/SILAR_PRD.docx`.
- Acuan Teknis SILAR rancangan versi **0.3**: `docs/architecture/SILAR_Technical_Reference.docx`, termasuk Lampiran A dan Digital Awareness pada A7.8.
- Identitas kebutuhan dan kriteria penerimaan mengikuti PRD: **FR01–FR26 / AC-F01–AC-F26** serta **NFR01–NFR10 / AC-N01–AC-N10**.

Keputusan perencanaan dicatat pada **MEET_05**. Pemetaan lengkap tersedia pada `SILAR_Pemetaan_Fitur_Final.md`. Status Done berlaku untuk ruang lingkup tahap masing-masing; penerimaan seluruh kebutuhan lintas card diverifikasi pada SLR_15.

# SLR_07 – Perancangan UI/UX dan Prototype SILAR

## Tujuan

Merancang antarmuka, interaksi dan prototype SILAR yang dapat digunakan kelompok sebagai pedoman implementasi, berdasarkan PRD versi 0.5, Acuan Teknis versi 0.3 dan pemetaan fitur final.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | — |
| NFR utama | NFR05, NFR06 |
| FR pendukung | FR01, FR02, FR03, FR04, FR05, FR06, FR07, FR08, FR09, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26 |
| NFR pendukung | NFR02, NFR03 |
| Acuan penerimaan utama | AC-N05, AC-N06 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan hasil SLR_04–SLR_06. Desain menjadi acuan frontend SLR_10–SLR_14. SLR_08 dan SLR_09 dapat berjalan paralel dengan perancangan ini menggunakan kontrak SLR_06.

## Task Detail

- [ ] Meninjau PRD, Acuan Teknis, kontrak API dan pemetaan FR01–FR26 serta NFR01–NFR10.
- [ ] Menyusun daftar layar, navigasi dan alur akun, Reporter, Operator, Admin serta Portal Publik; memetakan setiap kebutuhan ke layar, interaksi atau perilaku sistem yang relevan.
- [ ] Menetapkan perangkat/browser sasaran, ukuran tampilan dan kriteria responsif sesuai NFR06.
- [ ] Merancang alur FR01 dan FR02: registrasi, login, verifikasi email OTP, aktivasi Operator, resend dan reset akses, termasuk kode salah/kedaluwarsa serta bantuan akun.
- [ ] Merancang FR03 dan FR04: draft online, input teks/audio/gambar, validasi, upload, pemilihan bukti, Evidence Bundle dan pembacaan kembali bukti yang sudah terunggah sebelum bundle dibuat.
- [ ] Merancang tampilan FR05, FR06, FR07, FR08, FR09 dan FR10: proses analisis, bukti/narasi/hasil, NON_EVENT, uncertain, kegagalan dan pembacaan keadaan backend sesudah kehilangan respons.
- [ ] Merancang FR11, FR12, FR13, FR14 dan FR15: pemeriksaan Reporter, koreksi, riwayat versi, konfirmasi, submit eksplisit, status dan notifikasi dalam aplikasi.
- [ ] Merancang FR16, FR17, FR18, FR19, FR20, FR23, FR24 dan FR26: antrean, klaim, review, tindak lanjut, penugasan, keputusan internal/publikasi, audit berizin, close dan monitoring layanan.
- [ ] Merancang FR21 dan FR22: kandidat publikasi, sanitasi, approval versi tepat, pembatalan kandidat aktif serta Portal Publik dengan daftar/detail/pencarian/filter.
- [ ] Merancang FR25: instalasi PWA, tampilan dasar offline dan pemberitahuan bahwa operasi laporan memerlukan koneksi.
- [ ] Merancang keadaan kosong, loading, berhasil, input tidak valid, akses ditolak, konflik versi, offline, RUNNING dan UNKNOWN sesuai kontrak; pesan menyebut tindakan berikutnya tanpa menyatakan hasil yang belum diketahui.
- [ ] Menerapkan NFR05 dan Digital Awareness pada tindakan relevan: kepemilikan bukti, privasi, batas kategori, pemrosesan Gemini, keterbatasan AI, keamanan akun, sanitasi publik dan bantuan pemulihan.
- [ ] Membuat wireframe, rancangan layar dan prototype interaktif yang menelusuri alur utama serta keadaan penting menggunakan data contoh.
- [ ] Menyusun docs/uiux/README.md berisi daftar layar, pemetaan kebutuhan, alur, perilaku interaksi, referensi API, perangkat/browser sasaran, tautan/file sumber desain, prototype dan catatan review; ekspor PDF/PNG dapat ditambahkan sebagai referensi visual.
- [ ] Melakukan review kelompok, mencatat temuan dan memperbaiki rancangan; mempertahankan sumber desain yang dapat diedit dan mencatat bukti perubahan dokumentasi.

## Batasan Pekerjaan

Cakupan card adalah perancangan, simulasi interaksi dan dokumentasi UI/UX. Implementasi frontend/backend, migration, pelatihan model dan deployment mengikuti card masing-masing. Prototype tidak menjadi bukti layanan AI atau API telah berjalan.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Sumber desain dan wireframe/rancangan layar yang dapat diedit.
- File atau URL prototype interaktif.
- docs/uiux/README.md beserta pemetaan layar/kebutuhan/API dan perangkat sasaran.
- Catatan review, tindak lanjut, dan commit dokumentasi apabila sudah dibuat kelompok.

## Kriteria Selesai

Seluruh task dicentang; alur utama serta keadaan penting dapat ditelusuri; pemetaan kebutuhan tersedia; tampilan pada perangkat sasaran diperiksa; sumber desain, prototype dan README tersedia; hasil review ditindaklanjuti. Dokumen Word menjadi pilihan kelompok apabila diperlukan.

# SLR_08 – Implementasi Fondasi Backend dan Database SILAR

## Tujuan

Menyiapkan database, layanan akun, autentikasi, kontrol akses dan audit bersama sebagai fondasi implementasi fitur sesuai ERD, Data Dictionary dan kontrak API.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | FR01, FR23 |
| NFR utama | NFR01 |
| FR pendukung | FR02, FR03, FR04, FR10, FR13, FR15, FR16, FR17, FR18, FR19, FR21, FR24, FR25, FR26 |
| NFR pendukung | NFR02, NFR04, NFR10 |
| Acuan penerimaan utama | AC-F01, AC-F23, AC-N01 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan PRD dan Lampiran A Acuan Teknis hasil SLR_06. Dapat berjalan paralel dengan SLR_07 dan SLR_09; fondasi ini digunakan SLR_10–SLR_14.

## Task Detail

- [ ] Menyiapkan Django, DRF, environment dan koneksi PostgreSQL; menetapkan versi paket berdasarkan kompatibilitas dan mencatatnya.
- [ ] Menetapkan Custom User UUID sebelum migration awal, email unik yang dinormalisasi, Group/Permission, auth_version dan konfigurasi blacklist JWT sesuai rancangan.
- [ ] Mengimplementasikan Django Models, foreign key, pointer siklik, constraint dan indeks mengikuti A4/A8; menjaga bukti, versi, assignment dan audit historis.
- [ ] Membuat serta menjalankan migration pada database uji, kemudian memeriksa constraint versi, assignment aktif, idempotency dan reservasi run/slot RUNNING atau UNKNOWN.
- [ ] Mengimplementasikan FR01: registrasi Reporter, login, verifikasi email OTP, resend, aktivasi akun dan reset akses sesuai challenge serta kontrak A6/A7.
- [ ] Mengimplementasikan access/refresh JWT, rotasi/logout/pencabutan, cookie dan CSRF sesuai rancangan; verifikasi email menjadi syarat akses fungsi laporan privat.
- [ ] Memverifikasi kode OTP salah/kedaluwarsa, pembatasan request dan respons aman; OTP verifikasi/aktivasi/reset dipisahkan dari 2FA login sesuai PRD.
- [ ] Menerapkan NFR01: pemeriksaan peran, izin, kepemilikan serta assignment pada baca, mutasi dan replay; menyiapkan pola pemeriksaan izin untuk layanan berikutnya.
- [ ] Menyiapkan storage media privat, lokasi aset model dan konfigurasi akses melalui backend sesuai rancangan.
- [ ] Menyiapkan pola validasi, whitelist payload, error response, expected_revision, transaksi dan ledger idempotency yang digunakan layanan fitur.
- [ ] Mengimplementasikan FR23: model serta layanan audit bersama yang mencatat aktor, peran, objek, versi dan waktu, dengan akses baca terbatas dan tanpa nilai rahasia.
- [ ] Memverifikasi migration, autentikasi, OTP, pembatasan akses dan pencatatan audit dasar menggunakan skenario yang sesuai kontrak.
- [ ] Mendokumentasikan konfigurasi, cara menjalankan backend, hasil verifikasi dan bukti commit pekerjaan kelompok.

## Batasan Pekerjaan

Cakupan card adalah fondasi database, akun, keamanan dan layanan bersama. Endpoint bisnis laporan, pipeline AI, antarmuka frontend serta aturan tindakan khusus dibangun pada SLR_10–SLR_14. Integrasi fitur menambahkan event audit melalui layanan bersama.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Kode backend, Django Models dan migration.
- Layanan akun/OTP/JWT, kontrol akses dan audit dasar.
- Hasil verifikasi constraint, autentikasi serta izin.
- Petunjuk menjalankan backend dan Commit SHA/URL setelah dibuat kelompok.

## Kriteria Selesai

Fondasi backend berjalan, migration dan constraint terverifikasi, FR01 tersedia pada layanan akun, akses privat dibatasi, layanan audit bersama tersedia, dan hasil verifikasi serta petunjuk menjalankan terdokumentasi. Penerimaan fitur yang melibatkan UI dan event bisnis dilengkapi pada card pendukung serta SLR_15.

# SLR_09 – Persiapan Data, Pelatihan, dan Evaluasi Model AI SILAR

## Tujuan

Menyiapkan, melatih sesuai kebutuhan, mengevaluasi dan memversikan aset SENA/NARA beserta adapter yang dapat digunakan dalam pipeline SILAR.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | — |
| NFR utama | NFR09 |
| FR pendukung | FR07, FR08, FR09 |
| NFR pendukung | NFR08 |
| Acuan penerimaan utama | AC-N09 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan kebutuhan narasi, label dan output pada PRD serta A4.22/A7.7 Acuan Teknis. Dapat berjalan paralel dengan SLR_07 dan SLR_08. Aset dan adapter teruji menjadi masukan SLR_11.

## Task Detail

- [ ] Memeriksa dua paket SENA dan NARA serta artefak pendukung yang tersedia; mencatat versi, konfigurasi, asal dan kelengkapan aset.
- [ ] Mendokumentasikan sumber/lisensi data dan model, anotasi, preprocessing, pembagian training/validation/test serta pencegahan kebocoran data sesuai NFR09.
- [ ] Memverifikasi input Unified Incident Narrative, label kategori dan NON_EVENT untuk dukungan FR07; memeriksa confidence dan keluaran model aktual.
- [ ] Memverifikasi label/span NARA serta pemetaan role dan informasi ke schema A4.22 untuk dukungan FR08; mempertahankan informasi yang tidak ditemukan tanpa nilai buatan.
- [ ] Menyiapkan kode/configuration pelatihan dan mencatat proses pelatihan aset; menjalankan pelatihan atau perbaikan yang diperlukan berdasarkan pemeriksaan aset dan evaluasi.
- [ ] Mengevaluasi SENA dan NARA pada data uji yang sesuai MVP; mendokumentasikan metrik, hasil, variasi input, kesalahan prediksi serta kasus salah NON_EVENT.
- [ ] Menentukan target mutu dengan dasar yang tercatat untuk penerimaan akhir, serta mencatat keterbatasan dataset dan model.
- [ ] Menyiapkan adapter teruji, contoh input/output, pemetaan field, validasi hasil, serta versi model/adapter yang dipakai SLR_11.
- [ ] Mengkalibrasi threshold confidence dan memverifikasi kemampuan deteksi ambiguity sebelum aturan uncertain digunakan; mencatat konfigurasi versi sesuai A4.22.1.
- [ ] Memeriksa kompatibilitas pemuatan dan inferensi pada lingkungan tujuan, kebutuhan dependensi serta sumber daya; mendokumentasikan batasnya.
- [ ] Memversikan aset model, konfigurasi, label dan kode pendukung; mengelola berkas besar melalui Git LFS sesuai kebutuhan repository.
- [ ] Melakukan review hasil bersama kelompok serta mendokumentasikan evaluasi, keputusan perbaikan dan bukti commit artefak yang relevan.

## Batasan Pekerjaan

Cakupan card adalah aset SENA/NARA, data, pelatihan/evaluasi dan adapter teruji. Integrasi runtime dengan backend berada pada SLR_11. Whisper dan Gemini tidak dilatih pada card ini. Hasil proyek lama menjadi rujukan asal, sedangkan evaluasi aset untuk MVP tetap dibuktikan.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Paket aset SENA/NARA, konfigurasi, label dan catatan versi.
- Dataset atau rujukan sumber/lisensi, anotasi/split dan kode/configuration pelatihan.
- Laporan evaluasi, contoh output adapter dan konfigurasi threshold.
- Catatan review serta Commit SHA/URL artefak yang relevan.

## Kriteria Selesai

Aset dan provenance tersedia; proses pelatihan dapat ditelusuri; evaluasi pada data uji MVP terdokumentasi; output adapter sesuai rancangan; versi serta konfigurasi threshold jelas; kesiapan pemuatan diverifikasi. Pelatihan ulang mengikuti temuan evaluasi dan kebutuhan perbaikan.

# SLR_10 – Implementasi Frontend dan Pelaporan Multimodal SILAR

## Tujuan

Menyiapkan frontend Vue, alur akun, input multimodal, draft dan Evidence Bundle serta PWA dasar sesuai prototype dan kontrak API.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | FR03, FR04, FR25 |
| NFR utama | NFR07 |
| FR pendukung | FR01, FR05, FR06, FR10, FR11, FR12, FR14, FR22, FR23 |
| NFR pendukung | NFR01, NFR02, NFR03, NFR04, NFR05, NFR06, NFR10 |
| Acuan penerimaan utama | AC-F03, AC-F04, AC-F25, AC-N07 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan desain SLR_07 dan fondasi akun/database SLR_08. Pengelolaan bukti menjadi masukan SLR_11; kerangka frontend digunakan SLR_12–SLR_14.

## Task Detail

- [ ] Menyiapkan Vue 3, Composition API, Vue Router, Vite, Fetch dan CSS serta layout, navigasi dan pembatasan halaman sesuai peran.
- [ ] Mengimplementasikan antarmuka pendukung FR01: registrasi, login, email OTP, resend, aktivasi/reset akses dan logout menggunakan layanan SLR_08.
- [ ] Mengimplementasikan FR03: membuat/melanjutkan draft secara online, formulir teks/audio/gambar PNG/JPEG dan kombinasi input dengan minimal satu kanal asli valid.
- [ ] Menerapkan validasi frontend/backend sesuai kontrak serta panduan format, koneksi, batas kategori, kepemilikan bukti dan pembatasan data pribadi.
- [ ] Mengimplementasikan FR04: upload dan penyimpanan bukti asli, metadata, akses media privat, pemilihan item serta pembentukan/versi Evidence Bundle.
- [ ] Mengimplementasikan daftar `GET /api/v1/reports/{r}/evidence/` untuk draft pemilik sebelum bundle terbentuk, termasuk pagination dan Cache-Control: no-store; pembacaan tidak membentuk bundle atau mengubah revision.
- [ ] Mengimplementasikan pemulihan draft setelah tab ditutup: membaca draft milik pengguna dan evidence yang sudah tersimpan, lalu membuat bundle melalui tindakan eksplisit tanpa upload ulang.
- [ ] Menerapkan NFR07: daftar memakai ringkasan dan pagination; detail/media diambil ketika dibutuhkan sesuai hak akses.
- [ ] Menghubungkan tombol/keadaan analisis dengan kontrak FR10; informasi pemrosesan Gemini tampil sebelum rute terkait; hasil nyata dan pemulihan analisis dilengkapi bersama SLR_11.
- [ ] Mengimplementasikan FR25: instalasi PWA, manifest/service worker, versi cache aset antarmuka dan pemberitahuan offline; API, token, draft, evidence serta hasil AI tidak masuk cache offline.
- [ ] Menerapkan tampilan responsif dan pesan/bantuan Digital Awareness sesuai rancangan SLR_07, termasuk keamanan akun serta langkah memperbaiki input.
- [ ] Memverifikasi alur akun, validasi, upload, pembacaan bukti sebelum bundle, kepemilikan media, draft online, pengambilan data dan batas PWA.
- [ ] Mendokumentasikan hasil implementasi/verifikasi dan mencatat bukti commit pekerjaan kelompok.

## Batasan Pekerjaan

Cakupan card adalah kerangka frontend, alur akun, input, draft, bukti dan PWA. Pembentukan hasil AI berada pada SLR_11; Incident Card/Human Verification pada SLR_12; dashboard pengelolaan serta Portal Publik pada SLR_13–SLR_14.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Kode frontend serta API draft/evidence/bundle.
- Bukti verifikasi upload, akses media, pagination dan pemulihan bukti sebelum bundle.
- Bukti tampilan responsif, alur akun dan PWA.
- Dokumentasi serta Commit SHA/URL setelah dibuat kelompok.

## Kriteria Selesai

Frontend terhubung ke fondasi akun/backend; input valid dan bukti tersimpan sebagai draft; evidence dapat dibaca kembali sebelum bundle tanpa upload ulang; akses privat terlindungi; daftar/detail mengikuti kebutuhan; PWA sesuai batas rancangan; hasil verifikasi terdokumentasi. Alur analisis penuh diterima bersama SLR_11.

# SLR_11 – Integrasi Pipeline AI SILAR

## Tujuan

Mengintegrasikan routing, narasi, SENA, NARA dan Fusion dalam satu request analisis, termasuk keterlacakan, finalisasi, idempotency serta pemulihan hasil.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | FR05, FR06, FR07, FR08, FR09, FR10 |
| NFR utama | NFR03, NFR10 |
| FR pendukung | FR04, FR11, FR12, FR13, FR23, FR26 |
| NFR pendukung | NFR01, NFR04, NFR05, NFR07, NFR08, NFR09 |
| Acuan penerimaan utama | AC-F05, AC-F06, AC-F07, AC-F08, AC-F09, AC-F10, AC-N03, AC-N10 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan fondasi SLR_08, aset/adapter teruji SLR_09 dan pengelolaan bukti SLR_10. Hasil dan draft awal Incident Card digunakan SLR_12; metadata layanan digunakan SLR_13.

## Task Detail

- [ ] Memuat aset model dan konfigurasi adapter tervalidasi; apabila konfigurasi belum siap, menolak analisis secara aman sesuai kontrak.
- [ ] Mengimplementasikan FR05: tujuh kombinasi kanal, perhitungan kanal asli valid, transkripsi audio lokal dan pemilihan Normalizer/Gemini sesuai rute.
- [ ] Mengimplementasikan FR06: pembentukan dan penyimpanan Unified Incident Narrative dengan referensi bukti/transkrip; informasi tidak tersedia tidak ditambahkan sebagai fakta.
- [ ] Mengimplementasikan FR07: inferensi SENA, label/confidence, NON_EVENT, referensi narasi dan versi model tersimpan.
- [ ] Mengimplementasikan FR08: inferensi NARA, hasil mentah dan normalized_output sesuai adapter/schema tervalidasi, termasuk hubungan run serta narasi.
- [ ] Mengimplementasikan FR09: Fusion serta penyimpanan draft awal Incident Card dengan sumber, versi, uncertain dan alasan sesuai konfigurasi SLR_09.
- [ ] Mengimplementasikan FR10 dalam satu request sinkron, termasuk persiapan run, reservasi kapasitas, jejak hasil parsial, finalisasi atomik dan respons sesudah commit.
- [ ] Menerapkan NFR03: payload Gemini hanya memuat input yang diperlukan rute; audio asli, data akun, token, kredensial, audit dan catatan internal tidak dikirim.
- [ ] Menerapkan NFR10 dan kontrak A7.4: idempotency key/scope/payload, pemeriksaan akses replay, expected_revision, penjagaan sumber berubah dan pencegahan inferensi/mutasi ganda.
- [ ] Mengimplementasikan daftar/detail request dan pembacaan run/hasil milik pengguna untuk menemukan respons yang hilang; GET tidak menjalankan kembali inferensi atau mengubah keadaan.
- [ ] Mengimplementasikan penanganan RUNNING, SUCCEEDED, FAILED dan UNKNOWN sesuai A7.5; RUNNING/UNKNOWN tidak diulang otomatis.
- [ ] Menyiapkan prosedur pemulihan teknis run tertinggal sesuai A7.5: pemeriksaan proses lama, fencing token, finalisasi dengan audit dan retry eksplisit sesudah keadaan sah.
- [ ] Menghubungkan keadaan loading/hasil/kegagalan dan pemulihan pada frontend SLR_10/SLR_12 dengan keadaan backend serta pesan tindakan berikutnya.
- [ ] Mencatat event audit melalui fondasi SLR_08 dan menyediakan metadata layanan aman untuk monitoring SLR_13.
- [ ] Memverifikasi tujuh rute, source/versi hasil, NON_EVENT/uncertain, input berubah, replay, response hilang, konflik serta kegagalan finalisasi; mencatat waktu proses untuk pengukuran SLR_15.
- [ ] Mendokumentasikan konfigurasi, integrasi, prosedur pemulihan, hasil verifikasi dan bukti commit pekerjaan kelompok.

## Batasan Pekerjaan

Cakupan card adalah pipeline dan draft awal hasil Fusion. UI pemeriksaan, koreksi dan konfirmasi berada pada SLR_12. Pelatihan model berada pada SLR_09. Rancangan tetap memakai satu request analisis; worker terpisah dan engine yang telah dihapus berada di luar cakupan.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Kode pipeline, adapter runtime dan integrasi backend/frontend.
- Contoh hasil tujuh rute beserta sumber dan versi model.
- Bukti verifikasi ledger/replay, finalisasi, konflik dan pemulihan.
- Catatan waktu proses, prosedur pemulihan teknis dan Commit SHA/URL.

## Kriteria Selesai

Tujuh rute berjalan sesuai rancangan menggunakan aset teruji; narasi, hasil dan draft awal tersimpan dengan referensi yang sah; respons berhasil mengikuti commit; replay serta kegagalan ditangani tanpa mutasi ganda; keadaan tak pasti ditampilkan dan dipulihkan sesuai kontrak; hasil verifikasi terdokumentasi.

# SLR_12 – Incident Card, Human Verification, dan Versioning SILAR

## Tujuan

Menyediakan pemeriksaan draft hasil pipeline, koreksi, riwayat versi, konfirmasi, pengiriman resmi dan notifikasi dalam aplikasi bagi Reporter.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | FR11, FR12, FR13, FR14, FR15 |
| NFR utama | NFR04 |
| FR pendukung | FR03, FR04, FR06, FR07, FR08, FR09, FR10, FR16, FR17, FR18, FR23, FR24, FR25 |
| NFR pendukung | NFR01, NFR02, NFR05, NFR06, NFR07, NFR10 |
| Acuan penerimaan utama | AC-F11, AC-F12, AC-F13, AC-F14, AC-F15, AC-N04 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan frontend/evidence SLR_10 dan hasil/draft awal SLR_11. Laporan resmi diteruskan ke SLR_13. Layanan notifikasi bersama digunakan kembali oleh SLR_13 dan SLR_14.

## Task Detail

- [ ] Menampilkan draft awal Incident Card hasil FR09 dari SLR_11 beserta kategori, informasi ekstraksi, narasi, sumber bukti, confidence dan penanda uncertain.
- [ ] Mengimplementasikan FR11: pemilik membandingkan bukti, narasi dan hasil sebelum konfirmasi; informasi yang tidak tersedia ditampilkan secara jelas.
- [ ] Mengimplementasikan FR12: koreksi sebelum pengiriman membentuk versi baru serta mempertahankan bukti asli dan hasil mentah AI.
- [ ] Menerapkan pemrosesan ulang sesuai perubahan: perubahan narasi memanggil SENA/NARA/Fusion; perubahan bukti mengikuti rute; koreksi field kartu mempertahankan sumber dan hasil mentah.
- [ ] Menerapkan penahanan NON_EVENT, larangan mengubah kategori untuk melewati penahanan, analisis ulang yang diperlukan dan penanda uncertain yang tetap tersedia.
- [ ] Mengimplementasikan FR13: Human Verification untuk versi aktif, konfirmasi ulang setelah revisi, submit eksplisit, penguncian versi resmi dan penolakan pengiriman versi yang tidak memenuhi syarat.
- [ ] Mengimplementasikan FR14: daftar/detail laporan milik Reporter, status, riwayat versi serta riwayat aman tanpa catatan internal petugas.
- [ ] Mengimplementasikan FR15: layanan notifikasi bersama, daftar/pembacaan notifikasi sesuai penerima, penandaan dibaca dan tampilan notifikasi dalam aplikasi; menyiapkan integrasi event bagi SLR_13/SLR_14.
- [ ] Menerapkan NFR04 serta idempotency/expected_revision pada koreksi, konfirmasi dan submit; mencegah versi, konfirmasi atau pengiriman ganda.
- [ ] Mengintegrasikan dukungan FR10: membaca daftar request serta keadaan laporan/hasil ketika kembali ke aplikasi; retry mengikuti keputusan backend.
- [ ] Menerapkan pesan Digital Awareness yang membedakan hasil AI, konfirmasi Reporter, pemeriksaan Operator serta publikasi, dan menjelaskan penguncian versi resmi.
- [ ] Mencatat audit tindakan melalui layanan SLR_08 dan memberi laporan resmi kepada antrean SLR_13 setelah submit yang sah.
- [ ] Memverifikasi koreksi, perubahan sumber, penahanan NON_EVENT, uncertain, versi konfirmasi, izin pemilik, submit ulang, akses riwayat dan notifikasi penerima.
- [ ] Mendokumentasikan hasil pekerjaan/verifikasi dan mencatat bukti commit kelompok.

## Batasan Pekerjaan

Cakupan card adalah antarmuka dan tindakan Reporter atas draft hasil SLR_11, versioning, submit serta layanan notifikasi bersama. Pembentukan awal Fusion berada pada SLR_11. Pemeriksaan petugas, publikasi dan pemicu notifikasi pengelolaan dilengkapi SLR_13–SLR_14.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Kode layanan/API serta antarmuka Incident Card, koreksi, verifikasi dan riwayat.
- Layanan serta tampilan notifikasi dalam aplikasi.
- Bukti verifikasi versi, NON_EVENT/uncertain, submit, izin dan pemulihan baca.
- Dokumentasi serta Commit SHA/URL setelah dibuat kelompok.

## Kriteria Selesai

Reporter dapat memeriksa serta mengoreksi draft, jejak versi tetap utuh, konfirmasi berlaku untuk versi tepat, submit sah mengunci versi resmi dan meneruskan laporan ke Operator, serta status/riwayat/notifikasi hanya dapat dibaca pihak berwenang. Pemicu notifikasi pengelolaan dan publikasi dilengkapi pada card pendukung.

# SLR_13 – Pengelolaan Laporan oleh Operator dan Admin SILAR

## Tujuan

Mengimplementasikan antrean, klaim, review, validasi, tindak lanjut, penugasan, keputusan internal/publikasi, penutupan dan monitoring sesuai kewenangan Operator/Admin.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | FR02, FR16, FR17, FR18, FR19, FR20, FR24, FR26 |
| NFR utama | — |
| FR pendukung | FR01, FR10, FR13, FR15, FR21, FR23 |
| NFR pendukung | NFR01, NFR02, NFR04, NFR05, NFR06, NFR07, NFR10 |
| Acuan penerimaan utama | AC-F02, AC-F16, AC-F17, AC-F18, AC-F19, AC-F20, AC-F24, AC-F26 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan fondasi akun/izin/audit SLR_08 dan laporan resmi serta layanan notifikasi SLR_12. SLR_14 melengkapi proses kandidat/penerbitan publikasi; pengujian guard publikasi/close dilakukan bersama SLR_14 dan SLR_15.

## Task Detail

- [ ] Mengimplementasikan dashboard Operator dan Admin sesuai desain SLR_07.
- [ ] Mengimplementasikan FR02: Admin mengelola akun dan izin Operator, aktivasi serta penonaktifan menggunakan layanan akun SLR_08 dan mempertahankan riwayat.
- [ ] Mengimplementasikan FR16: antrean ringkas laporan resmi yang belum diklaim dalam kewenangan, tanpa PII; klaim atomik menghasilkan satu penanggung jawab.
- [ ] Menerapkan pembatasan setelah assignment: detail privat, bukti dan tindakan hanya untuk penanggung jawab saat ini sesuai izin; ringkasan antrean mengikuti kontrak.
- [ ] Mengimplementasikan FR17: pembacaan versi resmi, bukti, narasi dan hasil AI tanpa menyunting isi Reporter atau hasil mentah.
- [ ] Mengimplementasikan FR18: review VALID/INVALID/INCONCLUSIVE, alasan, aktor/waktu, perubahan status serta tindak lanjut PENDING/DONE/CANCELLED sesuai guard.
- [ ] Mengimplementasikan FR19: monitoring laporan resmi, penugasan dan pengalihan oleh Admin dengan alasan serta assignment historis; izin administratif tidak otomatis memberi kewenangan Operator.
- [ ] Mengimplementasikan FR20: keputusan INTERNAL atau arah PREPARE sesuai hasil review dan izin; INVALID/INCONCLUSIVE tetap internal, dan keputusan layak publikasi belum menerbitkan laporan.
- [ ] Mengimplementasikan FR24: close eksplisit dengan review yang sah, tindak lanjut selesai/dibatalkan, publikasi INTERNAL/PUBLISHED serta tanpa kandidat aktif; CLOSED menolak mutasi dan tetap mengizinkan pembacaan sesuai hak.
- [ ] Mengimplementasikan FR26: pembacaan status/metadata layanan terukur sesuai izin tanpa rahasia, akses draft Reporter, perubahan model atau tindakan menjalankan ulang analisis privat.
- [ ] Mengimplementasikan antarmuka baca audit FR23 sesuai izin menggunakan layanan bersama SLR_08; seluruh tindakan pengelolaan dicatat melalui layanan tersebut.
- [ ] Menambahkan pemicu notifikasi FR15 untuk assignment, perubahan relevan, penanganan dan penutupan melalui layanan SLR_12, sesuai penerima.
- [ ] Menerapkan expected_revision, transaksi, pemeriksaan akses replay dan perlindungan terhadap klaim/pengalihan/penutupan berulang.
- [ ] Memverifikasi hak akses, klaim bersamaan, hilangnya akses setelah pengalihan, tiga hasil review, tindak lanjut, keputusan INTERNAL dan close; memeriksa guard setelah publikasi bersama SLR_14.
- [ ] Mendokumentasikan hasil pekerjaan/verifikasi dan mencatat bukti commit kelompok.

## Batasan Pekerjaan

Cakupan card adalah pengelolaan laporan resmi dan keputusan arah publikasi. Kandidat, sanitasi, approval dan penerbitan berada pada SLR_14. Monitoring Admin bersifat baca; pemulihan run tertinggal mengikuti prosedur teknis SLR_11.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Kode dashboard, API akun/assignment/review/tindak lanjut/close dan monitoring.
- Antarmuka baca audit serta integrasi event audit/notifikasi.
- Bukti verifikasi klaim, pengalihan, akses, status dan guard close.
- Dokumentasi serta Commit SHA/URL setelah dibuat kelompok.

## Kriteria Selesai

Tindakan Operator/Admin sesuai PRD dan kontrak; klaim/assignment konsisten; status, alasan, audit serta notifikasi tercatat; monitoring aman; keputusan internal dan close dapat diverifikasi. Perilaku publikasi serta guard lintas alur dilengkapi SLR_14 dan diuji menyeluruh pada SLR_15.

# SLR_14 – Publikasi Aman dan Portal Publik SILAR

## Tujuan

Mengimplementasikan kandidat publikasi, sanitasi, approval, penerbitan dan Portal Publik yang hanya membaca informasi aman sesuai keputusan Operator.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | FR21, FR22 |
| NFR utama | NFR02 |
| FR pendukung | FR15, FR18, FR20, FR23, FR24 |
| NFR pendukung | NFR01, NFR04, NFR05, NFR06, NFR07, NFR10 |
| Acuan penerimaan utama | AC-F21, AC-F22, AC-N02 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan laporan resmi SLR_12 serta review, assignment dan keputusan arah publikasi SLR_13. Menggunakan layanan audit SLR_08 dan notifikasi SLR_12.

## Task Detail

- [ ] Menerapkan arah keputusan FR20 dari SLR_13 beserta izin penanggung jawab, review VALID dan guard status; keputusan persiapan tidak langsung menerbitkan laporan.
- [ ] Mengimplementasikan FR21: backend membentuk kandidat representasi publik dari sumber yang sah sesuai kontrak.
- [ ] Mengimplementasikan sanitasi dan NFR02: allowlist publik, pemeriksaan identitas/kontak/alamat privat serta risiko identifikasi dari kombinasi ringkasan, lokasi, waktu dan dampak.
- [ ] Menyediakan koreksi field publik, approval untuk versi kandidat tepat dan penerbitan atomik, dengan sumber internal serta bukti asli tetap utuh.
- [ ] Mengimplementasikan pembatalan kandidat aktif DRAFT/APPROVED dengan alasan, aktor/waktu, status dan audit sesuai kontrak; versi yang sudah terbit mengikuti aturan MVP.
- [ ] Mengimplementasikan kandidat pengganti sebelum CLOSED: versi terbit lama tetap tampil sampai pengganti disetujui dan diterbitkan; review serta versi resmi tidak berubah.
- [ ] Mengimplementasikan FR22: API dan tampilan daftar/detail/pencarian/filter hanya pada proyeksi publik yang sudah terbit, dengan pagination dan data sesuai kebutuhan.
- [ ] Menyediakan penjelasan asal informasi, pembedaan waktu kejadian/publikasi dan bahasa yang faktual sesuai Digital Awareness.
- [ ] Menolak mutasi publikasi setelah CLOSED; menghubungkan status/candidate guard dengan close FR24 pada SLR_13.
- [ ] Mencatat event publikasi/pembatalan melalui audit FR23 SLR_08 serta pemicu notifikasi FR15 melalui layanan SLR_12.
- [ ] Menerapkan transaksi, expected_revision, idempotency dan pemeriksaan akses sesuai kontrak untuk tindakan publikasi.
- [ ] Memverifikasi sanitasi antarfield, approval versi tepat, pembatalan kandidat, penggantian versi, pencarian publik, akses media privat serta mutasi setelah CLOSED.
- [ ] Mendokumentasikan hasil pekerjaan/verifikasi dan mencatat bukti commit kelompok.

## Batasan Pekerjaan

Cakupan card adalah representasi publik dan layanan baca Portal Publik. Laporan internal serta bukti asli tetap berada pada akses privat. Penarikan versi yang telah terbit dan perubahan review sesudah publikasi mengikuti batas MVP pada PRD, bukan fitur tambahan.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Kode kandidat, sanitasi, approval/penerbitan dan API/antarmuka Portal Publik.
- Contoh Public Incident Card yang disetujui menggunakan data uji.
- Bukti verifikasi privasi, versi, pencarian, pembatalan dan guard CLOSED.
- Dokumentasi serta Commit SHA/URL setelah dibuat kelompok.

## Kriteria Selesai

Informasi terbit hanya melalui kandidat tersanitasi dan approval versi tepat; Portal Publik hanya membaca allowlist; data privat terlindungi; pembatalan/penggantian versi sesuai kontrak; audit/notifikasi dan guard close konsisten; hasil verifikasi terdokumentasi.

# SLR_15 – Pengujian Sistem SILAR

## Tujuan

Memverifikasi penerimaan seluruh FR01–FR26 dan NFR01–NFR10 pada implementasi yang terintegrasi, serta mengukur kapasitas dan mencatat limitasi nyata.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | — |
| NFR utama | NFR08 |
| FR pendukung | FR01, FR02, FR03, FR04, FR05, FR06, FR07, FR08, FR09, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26 |
| NFR pendukung | NFR01, NFR02, NFR03, NFR04, NFR05, NFR06, NFR07, NFR09, NFR10 |
| Penerimaan terintegrasi | Seluruh FR01–FR26 dan NFR01–NFR10 |
| Acuan penerimaan utama | AC-N08 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Skenario disusun sejak perancangan SLR_07. Penerimaan akhir menggunakan implementasi/aset SLR_08–SLR_14 yang siap diintegrasikan; hasil pengujian menjadi dasar SLR_16.

## Task Detail

- [ ] Menyusun matriks uji FR01–FR26/AC-F01–AC-F26 dan NFR01–NFR10/AC-N01–AC-N10, termasuk skenario normal, ditolak, konflik dan pemulihan.
- [ ] Menguji FR01/FR02: akun, JWT/cookie/CSRF, OTP/challenge, resend, aktivasi/reset, izin Operator/Admin dan respons aman.
- [ ] Menguji FR03/FR04: tujuh kombinasi input, format/validasi, draft, bukti privat, bundle serta upload sukses dengan tab tertutup sebelum bundle dibuat; GET tidak mengubah revision.
- [ ] Menguji FR05/FR06/FR07/FR08/FR09/FR10: routing, narasi, sumber hasil, model/adapter nyata, Fusion, satu request, NON_EVENT, uncertain dan hasil parsial.
- [ ] Menguji FR11/FR12/FR13/FR14: pemeriksaan, koreksi narasi/field/bukti, konfirmasi versi, analisis ulang, penguncian submit, status dan riwayat aman.
- [ ] Menguji FR15/FR16/FR17/FR18/FR19/FR20/FR23/FR24/FR26: notifikasi penerima, klaim bersamaan, assignment/pengalihan, review, tindak lanjut, keputusan internal, audit, close serta monitoring aman.
- [ ] Menguji FR21/FR22: sanitasi antarfield, approval versi tepat, pembatalan/penggantian kandidat, daftar/detail/pencarian/filter publik serta larangan mutasi sesudah CLOSED.
- [ ] Menguji FR25, NFR05, NFR06 dan NFR07 pada perangkat/browser sasaran: responsif, navigasi, panduan, on-demand, cookie dan batas PWA/offline.
- [ ] Menguji NFR01/NFR02/NFR03/NFR04: akses pada baca/mutasi/replay, media privat, allowlist publik, data Gemini dan keutuhan bukti/versi.
- [ ] Menguji NFR10: expected_revision, idempotency, replay, izin yang dicabut, response hilang, RUNNING/UNKNOWN, timeout, gangguan layanan dan prosedur pemulihan teknis tanpa mutasi ganda.
- [ ] Mengevaluasi NFR09 bersama hasil SLR_09 dan alur aktual: metrik, target, variasi teks/audio/gambar, kesalahan NON_EVENT, confidence/ambiguity serta keterbatasan model/dataset.
- [ ] Mengukur NFR08 pada lingkungan tujuan: waktu proses, CPU/RAM, kapasitas bersamaan, decoder, kuota/deadline layanan, API/proxy dan reservasi slot; menetapkan target penerimaan dengan dasar pengukuran sebelum penerimaan akhir.
- [ ] Memeriksa penerapan Digital Awareness: keamanan OTP/password/cookie, panduan bukti/privasi/Gemini, batas AI, asal informasi publik, sanitasi dan pesan pemulihan.
- [ ] Mencatat temuan, memperbaiki pada card pemilik fitur, menguji ulang bagian terdampak dan memperbarui keterlacakan hasil.
- [ ] Mendokumentasikan matriks penerimaan, pengukuran, limitasi serta bukti commit perbaikan kelompok.

## Batasan Pekerjaan

Cakupan card adalah verifikasi implementasi dan pengukuran. Temuan diperbaiki sesuai kebutuhan yang sudah disepakati; perubahan kebutuhan produk dicatat pada dokumen/card terkait sebelum menjadi acuan baru.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Matriks kebutuhan, skenario, hasil uji dan status perbaikan.
- Hasil benchmark serta target/limitasi yang mempunyai dasar pengukuran.
- Bukti pengujian ulang, Digital Awareness dan penerimaan alur utama.
- Commit SHA/URL perbaikan setelah dibuat kelompok.

## Kriteria Selesai

Seluruh kebutuhan mempunyai hasil uji dan bukti; kriteria penerimaan wajib terpenuhi; masalah yang menghalangi alur utama, akses dan konsistensi diperbaiki; target mutu/kapasitas dinilai terhadap pengukuran; hasil uji ulang serta limitasi akhir terdokumentasi.

# SLR_16 – Deployment, Dokumentasi, dan Demo SILAR

## Tujuan

Menjalankan SILAR pada fasilitas tujuan, menyelaraskan dokumentasi dengan implementasi dan menyiapkan demo seluruh peran berdasarkan hasil penerimaan.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | — |
| NFR utama | — |
| FR pendukung | FR26 |
| NFR pendukung | NFR01, NFR08 |
| Verifikasi deployment/demo | Alur fitur yang diterima pada SLR_15 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Persiapan lingkungan dapat dilakukan lebih awal berdasarkan Acuan Teknis. Deployment/demo akhir menggunakan hasil SLR_15 serta build/aset terverifikasi SLR_08–SLR_14.

## Task Detail

- [ ] Memeriksa lingkungan fasilitas dosen, akses, versi paket, dependensi decoder/model, kapasitas, storage, domain/HTTPS serta kebijakan backup/retensi yang diperlukan.
- [ ] Menyiapkan build frontend, backend API, PostgreSQL, media privat dan aset model/adapter versi yang diterima.
- [ ] Mengatur environment, kredensial layanan, email OTP/pengirim resmi, JWT/cookie/CSRF, HTTPS dan izin storage sesuai konfigurasi yang diverifikasi.
- [ ] Menjalankan migration serta menyiapkan akun/demo sesuai izin Reporter, Operator dan Admin.
- [ ] Memverifikasi alur inti, login/OTP, media privat, sanitasi publik, notifikasi, PWA, timeout/kapasitas serta monitoring pada lingkungan deployment.
- [ ] Memeriksa prosedur backup/pemulihan dan run tertinggal, mempertahankan bukti/versi/audit serta mencatat parameter operasional yang telah divalidasi.
- [ ] Memperbarui README, Acuan Teknis dan dokumentasi UI/UX agar sesuai implementasi akhir; mencatat versi build/model serta batas yang telah diuji.
- [ ] Menyusun panduan penggunaan dan skenario demo yang memetakan fitur ke FR/AC serta card terkait, termasuk pesan Digital Awareness.
- [ ] Melaksanakan demo Reporter, Operator, Admin dan Portal Publik menggunakan data uji yang sesuai; mencatat hasil dan tindak lanjut.
- [ ] Mencatat alamat akses, hasil smoke test/demo, dokumentasi serta Commit SHA/URL release akhir yang dibuat kelompok.

## Batasan Pekerjaan

Cakupan card adalah deployment, dokumentasi dan demo fitur yang telah diterima. Pengembangan fitur tambahan mengikuti keputusan kebutuhan dan card yang sesuai.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- URL atau alamat akses deployment.
- Konfigurasi versi dan petunjuk operasional tanpa nilai rahasia.
- README, Acuan Teknis, dokumentasi UI/UX dan panduan penggunaan yang sesuai implementasi.
- Bukti verifikasi/demo dan Commit SHA/URL release setelah dibuat kelompok.

## Kriteria Selesai

Aplikasi dapat diakses pada lingkungan tujuan; alur utama dan konfigurasi penting berhasil diverifikasi; dokumentasi mencerminkan implementasi; parameter operasional serta prosedur pemulihan tercatat; demo selesai dan tindak lanjut yang menghalangi penggunaan ditangani.
