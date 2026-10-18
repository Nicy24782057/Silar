# Database dan layanan bersama

## Inventaris A4

Custom User ditetapkan sebelum migration awal. Seluruh ID entitas aplikasi UUID; Group/Permission dan tabel framework menggunakan aturan framework.

| Kelompok | Model |
| --- | --- |
| Akun | User, EmailOTP |
| Sumber | Report, EvidenceItem, EvidenceBundle, EvidenceBundleItem, Transcript, NarrativeVersion |
| Analisis dan versi | AnalysisRun, SENAResult, NARAResult, IncidentCardVersion, HumanVerification |
| Penanganan | OperatorAssignment, OperatorReview, FollowUpRecord |
| Publikasi/komunikasi/audit | PublicationVersion, Notification, AuditEvent |
| Ledger teknis A4.21 | IdempotencyRecord |
| Counter teknis implementasi | SecurityThrottle |

Ada 19 entitas bisnis A4.2–A4.20, satu ledger A4.21 dan satu counter teknis tambahan. SecurityThrottle menyimpan key HMAC, waktu window dan hitungan, tanpa IP/email mentah. Tabel blacklist JWT disediakan Simple JWT. Tidak ada model kandidat kejadian terkait, pertanyaan adaptif, penilaian kelengkapan atau antrian worker.

Migration: `accounts/0001_initial` membuat Custom User/OTP/counter; `core/0001_initial` membuat model dan menambahkan pointer siklik setelah target tersedia; `core/0002_history_guards` memasang penjagaan riwayat; `core/0003_nara_normalization_warnings` melengkapi metadata adapter; `core/0004_allowed_enums` menegakkan set nilai enum. Semua telah dijalankan pada database PostgreSQL 16 kosong. Perubahan skema tidak memerlukan pembuatan migration ulang oleh penerima paket.

## Integritas yang sudah dijaga

Constraint menegakkan email normal/unik, revisi/versi positif, versi unik per laporan, satu konfirmasi per kartu, satu SENA/NARA per run, satu narrative producer per run, satu assignment aktif, actor/key ledger unik, confidence 0–1, status enum dan metadata status terminal. Partial unique run per Report dan slot berlaku untuk **RUNNING maupun UNKNOWN**. SQL trigger melindungi bukti, bundle, keanggotaan, transkrip, narasi, hasil model, kartu, konfirmasi, review dan audit dari UPDATE/DELETE langsung.

Bundle dan item harus dibuat dalam transaksi yang sama dan tidak boleh commit kosong. Kolom internal database `_silar_creation_txid` merekam transaksi pembentukan bundle agar tambahan anggota setelah commit ditolak, termasuk ketika pembentukan memakai savepoint. Kolom ini bukan field bisnis/API; dikelola migration saja. Trigger juga membekukan sumber resmi setelah submit, menjadikan CLOSED terminal, melindungi identitas/riwayat assignment, mempertahankan jejak ledger/publikasi dari DELETE serta menolak perubahan isi kandidat yang memerlukan versi baru.

Validasi lintas sumber di `clean()` memeriksa kesamaan laporan, narasi SENA/NARA, asal koreksi pemilik, kategori kartu dari SENA dan penanda uncertain. JSON memisahkan hasil NARA tanpa `event_type` dari kartu yang menambahkan kategori SENA. `normalization_warnings` mempertahankan objek `{code,field}` hasil adapter, bukan membuat label mentah model. Field tidak ditemukan tetap `null`/`[]`; korban kosong tidak diartikan nol korban. SLR_09 tetap wajib membuktikan artefak dan adapter aktual.

Model/constraint adalah fondasi. Aturan layanan khusus—batas kanal bundle, validasi decoder/MIME/ukuran, finalisasi hasil lengkap, konfirmasi versi aktif, guard close/review/publikasi, proyeksi detail dan notifikasi—harus diterapkan pemilik endpoint pada SLR_10–SLR_14. Jangan memakai ORM/bulk SQL sebagai pengganti service berizin. Update/queryset dapat melewati `clean()`; gunakan jalur layanan dan transaksi sesuai kontrak.

## Izin dan storage

`core.permissions` membaca grant user/group dari database pada setiap pemeriksaan. Katalog hanya 13 codename A5.7; `is_superuser` tidak menjadi jalan pintas izin aplikasi. Role Admin tidak memberikan kewenangan Operator otomatis. Monitoring Admin tidak membuka draft; isi resmi memerlukan `monitor_report` dan `view_private_evidence`, atau grant Operator terpisah serta assignment aktif. Penanggung jawab lama kehilangan akses pada pembacaan berikutnya.

Gunakan `require_admin`, `require_operator`, `require_report_read`, `require_owner_draft` dan `require_handler` sesuai tindakan. `require_handler` memerlukan izin tindakan, scope isi, assignment saat ini dan belum CLOSED. Keputusan ini harus dipanggil kembali sebelum replay atau membaca media/versi, bukan hanya saat membuka menu.

`core.storage.store_validated_media` menyimpan konten yang **sudah lolos validasi SLR_10** dengan key acak dan permission privat. Helper tidak melakukan decoder atau validasi upload. `private_media_response` memeriksa scope isi serta path dan mengirim attachment/no-store. Backend tidak memasang route static untuk `private_media`, `private_outbox` atau `model_assets`; tidak ada URL publik untuk file privat. Endpoint media SLR_10 perlu serializer metadata yang tidak membuka `file_key`.

## Audit atomik

`core.audit.record_event` wajib dipanggil di dalam `transaction.atomic` yang sama dengan mutasi. Aktor, role snapshot, report, object/type/id, metadata sebelum/sesudah dan request ID dicatat. Sebelum/sesudah hanya menerima whitelist metadata, tanpa password, token, kode, kredensial, isi bukti atau narasi. Setiap layanan fitur menambahkan event pada perubahan yang benar-benar berhasil commit.

Ketika Admin bertindak sebagai penanggung jawab melalui grant Operator, panggil `acting_role="OPERATOR"` setelah guard tindakan. Helper memerlukan grant baca tugas dan assignment aktif untuk snapshot tersebut. Pengelolaan akun/assignment oleh Admin tetap mencatat ADMIN. Aktor sistem memakai `actor=None` dan SYSTEM. API audit hanya GET untuk Admin `view_audit`, dengan pagination dan filter `report_id`, `actor_id`, `action`.

## Revision dan idempotency

`core.mutations.atomic_mutation` adalah primitif mutasi transaksi singkat. Caller menyediakan actor, UUID key, scope backend, payload kanonis, report/expected_revision serta callback `authorize` dan `apply`. Urutan: lock akun/Report → periksa izin terkini → cari key → periksa scope/hash dan status → replay terminal sah → baru periksa expected_revision untuk tindakan baru → apply/perubahan/audit/ledger commit bersama.

Callback `apply` mengembalikan MutationResult dan bertanggung jawab menaikkan revision, menegakkan guard bisnis serta menyusun envelope Mutation A6. Callback tidak boleh menjalankan AI, mengirim email atau melakukan operasi jaringan panjang. `result.replayed` dipakai view untuk menambahkan `Idempotency-Replayed: true`. Account auth tidak memakai helper/ledger ini.

Replay mengembalikan envelope terminal tersimpan, bukan membangun ulang snapshot dari keadaan terbaru. Window awal 24 jam; key kedaluwarsa ditolak `IDEMPOTENCY_EXPIRED`, rekaman tidak dihapus/didaur ulang. RUNNING/UNKNOWN menolak eksekusi baru. Izin lebih dahulu daripada replay. Helper menolak penyimpanan key rahasia seperti password/access/refresh/OTP pada payload/envelope.

## Kapasitas untuk SLR_11

`core.capacity.analysis_slot()` memegang advisory lock pada koneksi psycopg khusus sepanjang konteks eksekusi. Partial unique di database menjadi reservasi persisten; UNKNOWN tetap memegang slot meskipun sesi advisory lock terputus. Kapasitas awal satu. Slot yang terkunci/penuh menghasilkan CAPACITY_BUSY tanpa worker atau antrean terselubung.

`create_reserved_run` menyimpan reservasi RUNNING dengan execution token, sumber dan revision; helper ini hanya untuk pembentukan run baru **setelah** caller SLR_11 melakukan pemeriksaan/replay ledger sesuai A7.4. Ini bukan endpoint analisis lengkap dan bukan handler retry. Caller memegang `analysis_slot`, memeriksa grant/sumber terbaru, memisahkan transaksi reservasi dari inferensi sinkron, lalu memfinalisasi seluruh hasil atomik dengan fence token/input_revision.

`fail_known_run` memfinalisasi kegagalan yang diketahui dengan fence token; helper tidak boleh digunakan untuk menebak bahwa proses UNKNOWN sudah berhenti. Pemulihan UNKNOWN memerlukan bukti teknis proses lama sudah berhenti, pemeriksaan sumber dan prosedur recovery SLR_11/15. Tidak ada tombol Admin atau auto retry/release dalam paket ini. Success finalizer, adapter model, cache artefak dan pengukuran layanan diselesaikan SLR_11 bersama aset SLR_09.

## Rujukan framework

Perilaku paket diuji terhadap kode/dependency yang dikunci. Referensi primer: [Django custom user](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/), [constraint](https://docs.djangoproject.com/en/5.2/ref/models/constraints/), [CSRF](https://docs.djangoproject.com/en/5.2/ref/csrf/), [DRF authentication](https://www.django-rest-framework.org/api-guide/authentication/), [Simple JWT blacklist](https://django-rest-framework-simplejwt.readthedocs.io/en/stable/blacklist_app.html), [PostgreSQL advisory lock](https://www.postgresql.org/docs/16/explicit-locking.html#ADVISORY-LOCKS).
