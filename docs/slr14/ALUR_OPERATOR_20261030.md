# Revisi alur Operator: review, pratinjau, dan publikasi

Umpan balik pengguna pada 30 Oktober 2026: review tersimpan terasa belum masuk,
alur keputusan/publikasi terlalu terpecah, serta perpindahan proses terasa
meloncat. Revisi ini memperjelas keberhasilan dan merangkai langkah yang sudah
ada. Kontrak API, izin, audit, model, migration, dan sembilan field publik tidak
berubah. Tujuh tab tetap tersedia.

## Alur yang terlihat oleh Operator

1. Operator menyimpan hasil dan alasan review. Aplikasi membaca ulang rincian
   dan mencocokkan review baru, laporan, versi resmi, petugas, hasil dan alasan.
   Setelah terbukti tersimpan, **Tindak Lanjut terbuka otomatis** dengan kartu
   **Review Anda sudah tersimpan**, hasil, versi resmi, dan waktu simpan.
   Isian review dikosongkan setelah keberhasilan, termasuk pada pemulihan respons.
2. Tindak lanjut dicatat bila diperlukan. Daftar beserta status tetap dapat
   dikelola. Tombol **Lanjut ke keputusan** tersedia; kembali melalui tombol atau
   tab tetap dimungkinkan sesuai izin. Tidak ada tindak lanjut fiktif yang dibuat.
3. Pada Keputusan, pilihan **Tinjau untuk publikasi** langsung menampilkan
   formulir beserta pratinjau yang mengikuti isian. Tidak ada tombol terpisah
   Siapkan publikasi atau Siapkan isi kandidat. Alasan keputusan tetap diperlukan.
   Nilai yang belum diketahui tetap kosong; kategori mengikuti kartu resmi.
4. Setelah menyunting isi publik, Operator memeriksa sanitasi dan mencentang
   pernyataan yang tersedia, lalu menekan **Konfirmasi isi publikasi**. Dalam alur
   normal, tindakan ini mencatat keputusan publikasi, menyimpan versi publik,
   membacanya, membandingkan isi tersimpan dengan isi pratinjau yang diperiksa,
   kemudian menyetujui versi yang tepat. Hasilnya adalah **Pratinjau terkonfirmasi**.
   Laporan **belum** terbit pada tahap ini.
5. Operator memastikan versi tersimpan dan menekan **Publikasikan sekarang**.
   Setelah hasil tersimpan terbaca, tampil keberhasilan beserta tautan ke Portal
   Publik. Tidak ada penerbitan otomatis atau draf pengganti otomatis setelahnya.
   Pembaruan berikutnya dimulai melalui **Tinjau pembaruan informasi**.

Dengan demikian, sesudah memeriksa pratinjau, alur normal memiliki dua aksi utama:
**Konfirmasi isi publikasi → Publikasikan sekarang**. Konfirmasi dan penerbitan
merupakan dua tindakan pengguna yang berbeda.

## Hubungan dengan kontrak yang sudah ada

| Tindakan pada layar | Operasi API yang tetap terpisah |
| --- | --- |
| Simpan review | POST workspace/reports/{id}/reviews/, lalu GET rincian |
| Konfirmasi isi publikasi | POST publication-decision/ bila belum PENDING_APPROVAL; POST publication-versions/; GET hasil; POST versi tepat /approve/; GET hasil |
| Publikasikan sekarang | POST versi tepat /publish/, lalu GET hasil |
| Batalkan draf publikasi | POST versi tepat /cancel/, dengan alasan |

Setiap POST memakai kunci idempotensi sendiri serta expected_revision dari
keadaan tersimpan terakhir. Konfirmasi merangkai operasi yang ada; tidak ada
endpoint baru dan tidak mengubah transisi backend. Sebelum approve pada alur
normal, aplikasi memeriksa ID versi, kartu resmi, kategori, keenam nilai publik,
dan bentuk tujuh field isi versi. Waktu dibandingkan sebagai instant yang sama.
Isi yang berbeda menghentikan persetujuan. Semua mutasi tetap diperiksa backend
untuk petugas aktif, penanggung jawab, izin, review Valid, dan revisi yang tepat.

Jika keputusan sudah tercatat, kelanjutan eksplisit tidak mencatatnya ulang.
Jika pembuatan versi gagal atau responsnya terputus, persetujuan tidak dijalankan
otomatis. Draf tersimpan yang dipulihkan ditampilkan untuk diperiksa dan
dikonfirmasi secara eksplisit. Penerbitan selalu menunggu tombol terakhir.
Kandidat pengganti tetap privat; versi terbit lama bertahan sampai penggantinya
benar-benar diterbitkan. Rantai versi tetap menunjuk parent terbaru, termasuk
versi yang dibatalkan.

## Perpindahan dan tampilan

- Pembacaan setelah penyimpanan dilakukan tanpa mengganti isi dengan blok
  loading besar. Hasil yang belum dapat dibaca tidak dilabeli berhasil.
- Perubahan tab dan tahap publikasi memakai fade/geser pendek dengan tinggi
  sementara, fokus ke judul tahap, dan scroll bila diperlukan. Elemen keluar
  tidak dapat diklik. Mode reduced motion menghilangkan animasi.
- Tab aktif yang berpindah otomatis digeser ke area terlihat pada navigasi
  ponsel. Penanda tab mempertahankan palet dan gaya acuan.
- Formulir dan pratinjau berdampingan di desktop, bertumpuk di layar kecil.
  Panel publikasi berada di bawah arah keputusan. Di ponsel publikasi tampil
  sebelum penutupan, mengikuti urutan kerja. Panel penutupan tetap memakai
  syarat resmi dari API dan tidak ditutup otomatis.
- Riwayat versi tetap tersedia melalui bagian yang dapat dibuka. Bukti, AI,
  sumber resmi, riwayat review, dan alur internal tetap dapat dibaca sesuai izin.

## Pemulihan kegagalan

Review ditolak tetap di formulir, dengan alasan yang telah diisi. Respons review
terputus menahan perpindahan hingga GET ledger dan rincian membuktikan hasilnya;
kemudian baru otomatis membuka Tindak Lanjut. Pemulihan tidak menambah POST.

Untuk publikasi, hasil belum pasti menyimpan referensi operasi, kunci dan body
aslinya. **Periksa hasil tindakan** memakai GET request dan keadaan terbaru.
Tindakan selanjutnya tidak dijalankan saat hasil sebelumnya belum pasti. Hanya
bila rekam request belum ditemukan, tersedia pemulihan eksplisit dengan kunci
serta body yang sama. Jika persetujuan gagal, draf tetap privat; publikasi tidak
berjalan. Isian dan pratinjau tidak diganti dengan informasi rekaan.

## Verifikasi revisi ini

| Pemeriksaan | Hasil | Bukti |
| --- | --- | --- |
| Unit frontend | 109 lulus, termasuk enam kasus alur Operator | bukti/frontend-unit.txt |
| Build produksi | Lulus | bukti/frontend-build.txt |
| Alur Operator + publikasi | 60 kombinasi render serta API lokal lulus | bukti/operator-alur-publikasi.txt |
| Kegagalan/pemulihan + tujuh tab | Lulus, termasuk 28 kombinasi tab/tema/lebar | bukti/operator-pemulihan.txt |
| PWA produksi | Lulus, 60 aset UI | bukti/pwa-operator.txt |

Enam lebar pada 60 kombinasi proses: 1440/1100/820/640/390/320, masing-masing
mode terang dan gelap. Lima keadaan: receipt review, formulir/pratinjau,
pratinjau terkonfirmasi, publikasi berhasil, serta draf pemulihan/pengganti.
Tidak ada error runtime atau luapan halaman/panel pada kasus yang diperiksa.

Pengujian membuktikan satu POST review, konfirmasi yang merangkai keputusan/
create/approve dengan isi dan revisi sesuai, tidak adanya GET publik sebelum
publish, dan keluaran publik tepat sembilan field. Respons publish dan create
terputus dipulihkan tanpa POST tambahan; versi pengganti lama tetap tersedia.
Kasus penolakan review, keputusan, approval 409, serta respons keputusan
terputus menghentikan tahap berikutnya. Form review kosong setelah pemulihan;
indikator tab otomatis terlihat di ponsel. Admin yang hanya membaca metadata
tetap memiliki lima tab dan tidak mendapatkan editor atau tombol publikasi.

API lokal memakai database QA terpisah; integritas diperiksa setelah suite.
PWA tidak menyimpan API, bukti, laporan, akun atau kredensial. Revisi ini tidak
menjalankan AI baru dan tidak mengubah backend. Hasil 94 tes backend komponen
serta batas PostgreSQL native dari audit sebelumnya tetap bersifat historis;
lihat [HASIL_VERIFIKASI.md](HASIL_VERIFIKASI.md).

Bukti visual terkini berawalan `bukti/operator-`. Ini pembaruan alur yang diminta
pengguna, bukan pernyataan bahwa seluruh aplikasi identik piksel dengan SVG.
Paket kumulatif dan petunjuk pemasangan ada pada `MULAI_DI_SINI.txt` serta
[README.md](README.md). Jika migration 0005 sudah terpasang, revisi Operator
ini tidak menambah migration atau dependensi.
