# Kontrak layanan input SLR_10

Base `/api/v1/`. Seluruh endpoint privat memerlukan akun aktif/terverifikasi dan Bearer access. Semua respons privat/media menggunakan Cache-Control no-store. Respons objek dibungkus `data`; daftar memakai `{count,next,previous,results}`.

| Method/path | Isi request | Hasil |
| --- | --- | --- |
| POST reports/ | JSON `{}`, Idempotency-Key UUID. | 201 Mutation: ReportSnapshot. |
| GET reports/ | scope, filter status, ordering, page/page_size sesuai A6.6. | 200 daftar ReportSummary. |
| GET reports/{r}/ | Tidak menerima query. | 200 ReportDetail sesuai izin. |
| POST reports/{r}/evidence/ | Multipart: type, expected_revision, text_content untuk TEXT atau satu file untuk IMAGE/AUDIO. Idempotency-Key. | 201 Mutation: Evidence. |
| GET reports/{r}/evidence/ | page/page_size; hanya Reporter pemilik pada NOT_SUBMITTED. | 200 daftar Evidence, termasuk di luar bundle. |
| GET evidence/{id}/media/ | Tidak menerima query; izin konten diperiksa ulang. | Byte file asli, MIME decoder, no-store. |
| POST reports/{r}/bundles/ | JSON evidence_ids berurutan, expected_revision. Idempotency-Key. | 201 Mutation: Bundle. |

GET evidence sesudah submit menghasilkan 422 TRANSITION_REJECTED bagi pemilik. Objek di luar ruang baca menghasilkan 404. Pembacaan tidak memutasi sumber. Sumber resmi setelah submit dibaca melalui detail/bundle yang diizinkan, bukan endpoint daftar evidence draft.

## Revision dan permintaan berulang

- Report baru memiliki revision/input_revision 1.
- Upload menaikkan revision, tanpa mengganti active_bundle atau input_revision.
- Bundle baru menaikkan revision dan input_revision, mengganti active_bundle serta menonaktifkan narasi/kartu sumber lama. Snapshot lama tetap tersimpan.
- Upload serial memakai revision terbaru dari respons mutasi. Jangan memakai satu revision yang sama untuk beberapa upload paralel.
- Idempotency actor/key/scope/payload yang sama mengembalikan snapshot terminal semula, dengan Idempotency-Replayed true, tanpa upload/bundle kedua. Izin diperiksa sebelum replay; guard revision/transisi tidak diterapkan ulang untuk replay sah.
- Key dengan payload/scope berbeda menghasilkan 409 IDEMPOTENCY_MISMATCH. Key kedaluwarsa tidak dipakai ulang. Frontend tidak melakukan retry mutasi otomatis.

## Mutasi dan audit

Respons mutasi berisi `data.report`, `data.result` dan `data.object`. Snapshot/revision diambil dari transaksi yang sama. Audit hanya menyimpan whitelist metadata. Media yang baru ditulis dihapus apabila transaksi upload gagal. Media tersimpan tetap privat dan bukti asli tidak diubah.

Schema ReportDetail dan helper serialisasi berada pada `reporting/serializers.py`. SLR_11 memakai model core yang sama sehingga hasil run/narasi/SENA/NARA/kartu yang sudah commit dapat dibaca oleh frontend tanpa memindahkan atau menggandakan model database.

## Kesalahan

400 schema/query/kanal; 401 identitas/token; 403 permission/CSRF; 404 scope/objek; 409 revision/idempotency; 413 ukuran/durasi; 415 media/decoder; 422 transisi. Decoder yang tidak tersedia menghasilkan 503 MEDIA_DECODER_NOT_READY. Error tidak berisi path fisik, body bukti, password, OTP atau kunci layanan.

Parameter awal mengikuti A7.3. Range audio tidak diimplementasikan pada penyajian FileResponse SLR_10; frontend mengambil satu blob privat ketika pengguna meminta media. Dukungan seeking/streaming lanjutan ditinjau saat integrasi, tanpa membuka URL publik.

## Profil audio revisi 1.1.0

Ekstensi/codec: WAV PCM, MP3/MP3, WebM/Opus, M4A/AAC, serta MP4/AAC. Berkas harus memiliki tepat satu stream audio dan tidak memiliki stream video, termasuk cover gambar. OGG, ALAC, Vorbis dan MP4 yang berisi video ditolak dengan MEDIA_UNSUPPORTED sebelum penyimpanan evidence/revision berubah. Batas tetap 10 MiB, lebih dari nol sampai 120 detik, satu audio per bundle dan 25 MiB total termasuk byte teks. Byte asli, hash dan metadata dipertahankan.

MIME canonical audio: audio/wav, audio/mpeg, audio/webm, audio/mp4. Alias container video/mp4 yang diberikan browser tidak mengizinkan video: validator tetap membuktikan AAC tanpa stream video dan menyimpan metadata audio/mp4. MIME lain yang tidak sesuai isi ditolak. Decoder yang belum tersedia tetap 503 MEDIA_DECODER_NOT_READY; kerusakan/codec tidak didukung tetap 415 MEDIA_UNSUPPORTED.
