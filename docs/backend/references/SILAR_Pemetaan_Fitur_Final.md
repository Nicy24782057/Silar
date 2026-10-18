# Pemetaan Fitur Final SILAR

**Versi pemetaan:** 1.0  
**Cakupan penyelarasan card:** SLR_07–SLR_16  
**Catatan keputusan:** MEET_05  
**Lokasi repository:** `docs/planning/SILAR_Pemetaan_Fitur_Final.md`

## Acuan

- PRD SILAR versi **0.5**: `docs/product/SILAR_PRD.docx`.
- Acuan Teknis SILAR rancangan versi **0.3**: `docs/architecture/SILAR_Technical_Reference.docx`, termasuk Lampiran A dan Digital Awareness pada A7.8.
- Identitas kebutuhan dan kriteria penerimaan mengikuti PRD: **FR01–FR26 / AC-F01–AC-F26** serta **NFR01–NFR10 / AC-N01–AC-N10**.

Nama kebutuhan pada tabel merupakan ringkasan untuk perencanaan. Definisi serta kriteria penerimaan lengkap tetap mengikuti PRD; pemetaan ini menetapkan penanggung jawab dan kontribusi pekerjaan.

## Keputusan Pemetaan

1. PRD SILAR versi 0.5 dan Acuan Teknis rancangan 0.3 menjadi acuan pemetaan; identitas FR01–FR26 dan NFR01–NFR10 digunakan pada card, desain, implementasi dan pengujian.

2. Setiap kebutuhan mempunyai satu card utama sebagai penanggung jawab integrasi/penerimaan kebutuhan serta card pendukung dengan kontribusi yang jelas. Card utama bukan pembatas bahwa seluruh pekerjaan harus berada di satu card.

3. Nomor dan judul tahapan SLR_01–SLR_16 digunakan sesuai susunan proyek. Penyesuaian dilakukan pada Task Detail, keterlacakan, dependensi, bukti dan kriteria selesai SLR_07–SLR_16.

4. Setiap task fitur menyebut ID kebutuhan dan hasil yang dapat diperiksa. Kriteria AC-F/AC-N dari PRD menjadi acuan verifikasi; status Done card berlaku untuk lingkup tahap tersebut, sedangkan penerimaan kebutuhan lintas card dilengkapi dan diuji pada SLR_15.

5. SLR_08 membangun layanan akun/keamanan dan audit bersama. SLR_11 membentuk narasi, hasil model, Fusion serta draft awal. SLR_12 menyediakan koreksi, verifikasi, submit, riwayat dan layanan notifikasi bersama. SLR_13/SLR_14 menambahkan pemicu dan tindakan pengelolaan/publikasi.

6. Keputusan INTERNAL atau arah PREPARE berada pada SLR_13. Kandidat, sanitasi, approval versi tepat dan penerbitan berada pada SLR_14. Guard close/publikasi diuji pada lingkup masing-masing serta integrasi SLR_15.

7. Hasil wajib SLR_07 adalah sumber desain yang dapat diedit, wireframe/rancangan layar, prototype interaktif serta docs/uiux/README.md yang memuat layar, alur, perilaku, kebutuhan/API, perangkat sasaran dan hasil review. Dokumentasi ini merupakan kebutuhan kelompok untuk mempermudah coding; Word menjadi pilihan bila diperlukan dan ekspor PDF/PNG dapat ditambahkan.

8. SLR_07 merancang keadaan normal, kosong, loading, gagal, akses ditolak, konflik versi, offline, NON_EVENT, uncertain, RUNNING/UNKNOWN dan pemulihan baca berdasarkan kontrak. Semua kebutuhan dipetakan ke layar/interaksi atau perilaku sistem yang relevan.

9. SLR_08 dan SLR_09 dapat dikerjakan paralel, termasuk saat SLR_07 berlangsung, dengan acuan format narasi, label, schema hasil, versi adapter/model dan lingkungan yang sama. Integrasi aktual membutuhkan fondasi SLR_08, aset teruji SLR_09 dan bukti dari SLR_10.

10. Digital Awareness diterapkan sebagai panduan serta perilaku fitur yang relevan pada akun, input, AI, verifikasi, publikasi dan pemulihan; keterlacakannya mengikuti FR/NFR serta A7.8. Penerapan ini tidak menambah kategori atau engine baru.

Fitur dicantumkan sebagai task ber-ID pada card tahapan SLR yang sesuai. Dengan demikian, hubungan **kebutuhan → card/task → hasil pekerjaan → bukti uji** dapat diperiksa di Kanban. SLR_01–SLR_06 tetap mengikuti hasil dan keputusan yang telah disepakati. Penyelarasan tahap berikutnya diterapkan pada isi card SLR_07–SLR_16 di GitHub Project.

## Kebutuhan Fungsional

Setiap FR mempunyai tepat satu card utama. Card pendukung mengerjakan kontribusi yang dijelaskan pada Task Detail masing-masing; hasil akhir diperiksa terhadap AC terkait pada SLR_15.

| Kebutuhan | Card utama | Card pendukung | Pembagian hasil pekerjaan | Acuan uji |
| --- | --- | --- | --- | --- |
| FR01 — Akun dan akses pengguna | SLR_08 | SLR_07, SLR_10, SLR_13, SLR_15 | Backend registrasi, login, email OTP, aktivasi, reset akses, resend, JWT dan pembatasan fungsi privat. Antarmuka akun dibuat di SLR_10; pengelolaan Operator di SLR_13. | AC-F01 |
| FR02 — Pengelolaan akun Operator | SLR_13 | SLR_07, SLR_08, SLR_15 | Admin mengelola akun, izin, aktivasi dan penonaktifan Operator menggunakan fondasi akun SLR_08. | AC-F02 |
| FR03 — Draft dan input multimodal | SLR_10 | SLR_07, SLR_08, SLR_12, SLR_15 | Formulir dan API draft online, minimal satu kanal valid, validasi, format PNG/JPEG serta panduan input. | AC-F03 |
| FR04 — Bukti asli dan Evidence Bundle | SLR_10 | SLR_07, SLR_08, SLR_11, SLR_12, SLR_15 | Upload dan pembacaan bukti privat, daftar evidence sebelum bundle, pemilihan item, bundle immutable serta sumber bukti yang dapat ditelusuri. | AC-F04 |
| FR05 — Pemilihan rute kanal | SLR_11 | SLR_07, SLR_10, SLR_15 | Tujuh kombinasi kanal; audio ditranskripsikan lokal; Gemini mengikuti rute yang disepakati. | AC-F05 |
| FR06 — Narasi berdasarkan sumber | SLR_11 | SLR_07, SLR_10, SLR_12, SLR_15 | Pembentukan dan penyimpanan Unified Incident Narrative tanpa menambah fakta, dengan referensi sumber. | AC-F06 |
| FR07 — Klasifikasi SENA | SLR_11 | SLR_07, SLR_09, SLR_12, SLR_15 | Inferensi SENA, label, confidence, versi model dan hasil tersimpan. SLR_09 menyiapkan model/adapter; SLR_12 menerapkan penahanan NON_EVENT pada pengiriman. | AC-F07 |
| FR08 — Ekstraksi NARA | SLR_11 | SLR_07, SLR_09, SLR_12, SLR_15 | Inferensi NARA dan pemetaan informasi ke schema yang dapat ditelusuri ke narasi, menggunakan adapter teruji dari SLR_09. | AC-F08 |
| FR09 — Fusion dan Incident Card | SLR_11 | SLR_07, SLR_09, SLR_12, SLR_15 | Fusion menghasilkan serta menyimpan draft awal Incident Card dan alasan uncertain. SLR_12 menampilkan, mengoreksi dan memverifikasi draft tersebut. | AC-F09 |
| FR10 — Satu request analisis | SLR_11 | SLR_07, SLR_08, SLR_10, SLR_12, SLR_13, SLR_15 | Eksekusi sinkron, finalisasi, idempotency, daftar request dan pemulihan hasil; UI membaca keadaan backend sebelum retry. | AC-F10 |
| FR11 — Pemeriksaan Reporter | SLR_12 | SLR_07, SLR_10, SLR_11, SLR_15 | Pemilik membandingkan bukti, narasi dan hasil AI sebelum memberikan konfirmasi. | AC-F11 |
| FR12 — Koreksi sebagai revisi | SLR_12 | SLR_07, SLR_10, SLR_11, SLR_15 | Koreksi sebelum submit menghasilkan versi baru; perubahan narasi/bukti memanggil pemrosesan ulang yang sesuai. | AC-F12 |
| FR13 — Konfirmasi dan pengiriman resmi | SLR_12 | SLR_07, SLR_08, SLR_11, SLR_13, SLR_15 | Konfirmasi berlaku untuk versi aktif; submit eksplisit mengunci versi resmi dan menolak NON_EVENT. | AC-F13 |
| FR14 — Status dan riwayat Reporter | SLR_12 | SLR_07, SLR_10, SLR_15 | Status, versi dan riwayat aman milik Reporter ditampilkan sesuai hak akses. | AC-F14 |
| FR15 — Notifikasi | SLR_12 | SLR_07, SLR_08, SLR_13, SLR_14, SLR_15 | Layanan dan tampilan notifikasi dalam aplikasi dibangun bersama riwayat Reporter. SLR_13 menambahkan pemicu assignment/status/penutupan; SLR_14 menambahkan pemicu publikasi. | AC-F15 |
| FR16 — Antrean dan klaim Operator | SLR_13 | SLR_07, SLR_08, SLR_12, SLR_15 | Ringkasan antrean tanpa PII, klaim atomik dan pembatasan detail sesudah assignment. | AC-F16 |
| FR17 — Review laporan resmi | SLR_13 | SLR_07, SLR_08, SLR_12, SLR_15 | Operator penanggung jawab membaca versi resmi dan bukti; isi Reporter serta hasil mentah AI tetap terlindungi. | AC-F17 |
| FR18 — Validasi dan tindak lanjut | SLR_13 | SLR_07, SLR_08, SLR_12, SLR_14, SLR_15 | VALID/INVALID/INCONCLUSIVE, alasan, tindak lanjut dan guard status; review dikunci setelah publikasi pertama. | AC-F18 |
| FR19 — Monitoring dan penugasan Admin | SLR_13 | SLR_07, SLR_08, SLR_15 | Monitoring laporan resmi, assignment dan pengalihan dengan izin, alasan serta jejak historis. | AC-F19 |
| FR20 — Keputusan internal atau publikasi | SLR_13 | SLR_07, SLR_14, SLR_15 | Operator menentukan INTERNAL atau arah PREPARE sesuai izin dan hasil review. Persiapan kandidat, approval dan penerbitan dikerjakan di SLR_14. | AC-F20 |
| FR21 — Sanitasi dan persetujuan publikasi | SLR_14 | SLR_07, SLR_08, SLR_13, SLR_15 | Kandidat versi publik, sanitasi antarfield, approval versi tepat, penerbitan dan pembatalan kandidat aktif sesuai kontrak. | AC-F21 |
| FR22 — Portal baca publik | SLR_14 | SLR_07, SLR_10, SLR_15 | Daftar, detail, pencarian dan filter hanya untuk field publik yang sudah diterbitkan. | AC-F22 |
| FR23 — Audit | SLR_08 | SLR_07, SLR_10, SLR_11, SLR_12, SLR_13, SLR_14, SLR_15 | Model dan layanan audit bersama dibangun pada fondasi backend. Setiap card fitur mencatat tindakan masing-masing; antarmuka baca audit berizin dibuat di SLR_13. | AC-F23 |
| FR24 — Penutupan laporan | SLR_13 | SLR_07, SLR_08, SLR_12, SLR_14, SLR_15 | Close eksplisit dengan review, tindak lanjut selesai/dibatalkan, publikasi INTERNAL/PUBLISHED dan tanpa kandidat aktif; CLOSED menolak mutasi. | AC-F24 |
| FR25 — PWA dasar | SLR_10 | SLR_07, SLR_08, SLR_12, SLR_15 | Instalasi, cache aset antarmuka dan pemberitahuan offline; data privat dan seluruh operasi laporan tetap online. | AC-F25 |
| FR26 — Pemantauan layanan | SLR_13 | SLR_07, SLR_08, SLR_11, SLR_15, SLR_16 | Admin membaca status/metadata layanan yang terukur sesuai izin, tanpa rahasia, akses draft Reporter atau kendali menjalankan ulang model. | AC-F26 |

## Kebutuhan Nonfungsional

Card utama menetapkan atau membangun dasar pemenuhan NFR. Implementasi pada alur terkait, pengukuran dan penerimaan akhir dilengkapi card pendukung. NFR05/NFR06 dirancang pada SLR_07, diterapkan pada card frontend, kemudian diuji pada SLR_15.

| Kebutuhan | Card utama | Card pendukung | Pembagian hasil pekerjaan | Acuan uji |
| --- | --- | --- | --- | --- |
| NFR01 — Kontrol akses backend | SLR_08 | SLR_10, SLR_11, SLR_12, SLR_13, SLR_14, SLR_15, SLR_16 | Izin, kepemilikan, assignment, OTP, JWT/cookie/CSRF dan pemeriksaan ulang akses pada replay. | AC-N01 |
| NFR02 — Privasi media dan publikasi | SLR_14 | SLR_07, SLR_08, SLR_10, SLR_12, SLR_13, SLR_15 | Media privat terlindungi dan publik memakai allowlist; sanitasi juga memeriksa identifikasi dari kombinasi field. | AC-N02 |
| NFR03 — Batas data Gemini | SLR_11 | SLR_07, SLR_10, SLR_15 | Data keluar mengikuti rute/D08; informasi pemrosesan eksternal tampil sebelum analisis. | AC-N03 |
| NFR04 — Keutuhan bukti dan versi | SLR_12 | SLR_08, SLR_10, SLR_11, SLR_13, SLR_14, SLR_15 | Bukti, hasil mentah, versi resmi dan jejak tindakan dipertahankan sepanjang alur. | AC-N04 |
| NFR05 — Kejelasan keputusan | SLR_07 | SLR_10, SLR_11, SLR_12, SLR_13, SLR_14, SLR_15 | Desain membedakan AI, konfirmasi Reporter, review Operator dan publikasi serta memberi panduan dan langkah pemulihan yang jelas. | AC-N05 |
| NFR06 — Antarmuka responsif | SLR_07 | SLR_10, SLR_12, SLR_13, SLR_14, SLR_15 | Perangkat/browser sasaran dan ukuran tampilan ditetapkan; alur utama tetap dapat digunakan tanpa kontrol tertutup. | AC-N06 |
| NFR07 — Pengambilan data sesuai kebutuhan | SLR_10 | SLR_11, SLR_12, SLR_13, SLR_14, SLR_15 | Daftar ringkas, pagination, detail/media/riwayat on-demand dan pembatasan akses setiap pembacaan. | AC-N07 |
| NFR08 — Kapasitas terukur | SLR_15 | SLR_09, SLR_11, SLR_16 | Benchmark lingkungan tujuan dan penetapan target penerimaan yang berdasar sebelum penerimaan akhir. | AC-N08 |
| NFR09 — Mutu AI dievaluasi | SLR_09 | SLR_11, SLR_15 | Sumber/lisensi/split data, versi, pelatihan, metrik, target, variasi input dan salah NON_EVENT dievaluasi pada aset yang digunakan. | AC-N09 |
| NFR10 — Konsistensi status dan respons | SLR_11 | SLR_08, SLR_10, SLR_12, SLR_13, SLR_14, SLR_15 | Transaksi, expected_revision, idempotency dan pemulihan dari keadaan backend tanpa mutasi ganda atau retry otomatis RUNNING/UNKNOWN. | AC-N10 |

## Digital Awareness

Penerapan mengikuti A7.8 dan ditempatkan pada fitur yang relevan. Setiap baris menghubungkan keputusan desain, implementasi dan verifikasi.

| Aspek | Kebutuhan terkait | Desain | Implementasi | Verifikasi | Hasil yang diperiksa |
| --- | --- | --- | --- | --- | --- |
| Akses dan koneksi | FR03, FR25, NFR06, NFR07 | SLR_07 | SLR_10 | SLR_15 | Pilihan kanal, panduan format/koneksi, tampilan sasaran, operasi online serta batas cache PWA. |
| Keamanan akun | FR01, NFR01, NFR05 | SLR_07 | SLR_08, SLR_10, SLR_13 | SLR_15, SLR_16 | Password/OTP dirahasiakan; panduan cookie dan pemulihan akses; pengirim/alamat resmi diverifikasi saat deployment. |
| Kepemilikan dan privasi bukti | FR03, FR04, NFR02 | SLR_07 | SLR_10, SLR_14 | SLR_15 | Panduan bukti milik Reporter, pembatasan data pribadi, bukti privat dan sanitasi antarfield. |
| Batas AI dan pemrosesan eksternal | FR05, FR06, FR07, FR08, FR09, FR10, FR11, FR12, FR13, NFR03, NFR05, NFR09 | SLR_07 | SLR_09, SLR_10, SLR_11, SLR_12 | SLR_15 | Informasi rute Gemini, sumber/lisensi/evaluasi, confidence/uncertain, salah NON_EVENT serta pembedaan keputusan AI/manusia. |
| Etika, sumber informasi dan publikasi | FR18, FR21, FR22, NFR02, NFR05 | SLR_07 | SLR_13, SLR_14 | SLR_15 | Bahasa faktual, pemeriksaan PII antarfield, asal laporan ditinjau, waktu kejadian/publikasi dan jejak salinan publik. |
| Jejak versi dan pemulihan | FR04, FR10, FR12, FR14, FR23, NFR04, NFR07, NFR10 | SLR_07 | SLR_08, SLR_10, SLR_11, SLR_12, SLR_13, SLR_14 | SLR_15 | Bukti/versi/audit dipertahankan; baca keadaan backend sebelum retry; bantuan menyebut tindakan berikutnya. |

## Keluaran SLR_07

- Sumber desain yang dapat diedit serta wireframe/rancangan layar.
- Prototype interaktif yang menelusuri alur utama dan keadaan penting dengan data contoh.
- `docs/uiux/README.md`: daftar layar, navigasi/alur, perilaku interaksi, pemetaan FR/NFR dan API, perangkat/browser sasaran, sumber desain/prototype, serta catatan review.
- Ekspor PDF/PNG dapat melengkapi referensi visual. Dokumen Word menjadi pilihan kelompok bila diperlukan.

Dokumentasi UI/UX ini ditetapkan oleh kelompok untuk mempermudah implementasi. Ketentuan dosen yang digunakan adalah keterlacakan setiap fitur pada Kanban dan kesesuaiannya dengan pekerjaan yang dibuat.

## Dependensi dan Pekerjaan Paralel

| Card | Prasyarat / masukan | Hasil tahap | Hubungan pekerjaan |
| --- | --- | --- | --- |
| SLR_07 | PRD dan SLR_06 | Perancangan serta prototype | Menjadi acuan antarmuka SLR_10–SLR_14; dapat paralel dengan SLR_08/SLR_09. |
| SLR_08 | PRD dan SLR_06 | Fondasi database/akun/izin/audit | Dapat paralel dengan SLR_07/SLR_09; hasil dipakai SLR_10–SLR_14. |
| SLR_09 | PRD, schema hasil SLR_06 dan aset model | Data, pelatihan/evaluasi dan adapter | Dapat paralel dengan SLR_07/SLR_08; aset teruji diperlukan pada integrasi SLR_11. |
| SLR_10 | Desain SLR_07 dan fondasi SLR_08 | Frontend akun, input, draft, bukti dan PWA | Endpoint bukti/bundle menjadi masukan SLR_11; UI analisis dilengkapi bersama SLR_11. |
| SLR_11 | SLR_08, SLR_09 dan pengelolaan bukti SLR_10 | Pipeline, draft awal, ledger dan pemulihan | Hasil aktual dipakai SLR_12; monitoring aman dipakai SLR_13. |
| SLR_12 | SLR_10 dan hasil SLR_11 | Reporter, versi, submit dan notifikasi bersama | Laporan resmi serta notifikasi menjadi masukan SLR_13/SLR_14. |
| SLR_13 | SLR_08 dan laporan resmi/layanan SLR_12 | Operator/Admin dan keputusan arah publikasi | SLR_14 melengkapi penerbitan; guard publikasi/close diverifikasi lintas alur tanpa membalik urutan fondasi. |
| SLR_14 | Review/assignment SLR_13 dan versi resmi SLR_12 | Kandidat, sanitasi, penerbitan dan portal | Menggunakan audit/notifikasi bersama; melengkapi guard close dan pemicu publikasi. |
| SLR_15 | Skenario dapat disiapkan sejak SLR_07; implementasi/aset terintegrasi SLR_08–SLR_14 untuk penerimaan akhir | Uji FR/NFR dan pengukuran | Temuan dikembalikan ke card pemilik; penerimaan akhir menjadi dasar deployment/demo. |
| SLR_16 | Persiapan lingkungan dapat lebih awal; build/aset diterima berdasarkan SLR_15 | Deployment, dokumentasi dan demo | Memverifikasi konfigurasi serta alur pada lingkungan tujuan. |

Prasyarat menunjukkan hasil atau komponen yang sudah tersedia dan dapat digunakan. Review, assignment serta keputusan arah publikasi SLR_13 menjadi masukan SLR_14; pengujian guard publikasi/close dilengkapi bersama setelah kedua alur tersedia.

SLR_08 dan SLR_09 menggunakan kontrak narasi, label, schema hasil dan versi model/adapter yang sama dari SLR_06. Kelompok menyepakati versi dependensi serta lingkungan eksekusi sebelum integrasi. Perubahan kontrak dicatat dan diselaraskan pada sumber acuan serta card yang terdampak.

## Aturan Penyelarasan Kanban

- MEET_05 ditempatkan pada kolom **Meeting**; tanggal diisi sesuai pelaksanaan meeting.
- Teks pekerjaan SLR_07–SLR_16 menggantikan isi card sesuai nomornya. Semua task awal belum dicentang.
- Task menyebut ID kebutuhan dan hasil yang dapat diperiksa. Kontribusi pendukung tercatat pada card terkait.
- Bukti diisi dengan hasil yang benar-benar tersedia; Commit SHA/URL dicatat setelah kelompok membuat commit.
- Done menilai hasil tahap. Kebutuhan lintas card memperoleh hasil penerimaan terintegrasi pada SLR_15.
- Usulan perubahan kebutuhan ditinjau dan dicatat pada acuan, pemetaan serta card terdampak sebelum diterapkan.

## Penyimpanan Dokumen dan Pencatatan Card

- Dokumen pemetaan fitur ini menjadi acuan bersama di `docs/planning/SILAR_Pemetaan_Fitur_Final.md` dan dimasukkan ke repository melalui commit serta push oleh kelompok.
- Catatan MEET_05 dicatat pada kolom Meeting di GitHub Project.
- Task, keterlacakan, dependensi, bukti dan kriteria selesai diperbarui pada card SLR_07–SLR_16 di GitHub Project.
- File bantu isi card dan checklist cukup digunakan sebagai bahan copy-paste kelompok.
- Dokumentasi UI/UX masuk `docs/uiux/` setelah hasil SLR_07 tersedia.
- Bukti MEET_05 mencantumkan dokumen pemetaan, pembaruan card pada GitHub Project serta commit setelah dibuat.

Berkas ini berisi hasil perencanaan. Bukti implementasi, pengujian dan deployment dihasilkan pada tahap pekerjaan masing-masing.
