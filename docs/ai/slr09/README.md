# SLR09 — lingkup aset dan kontrak AI

SLR09 menghasilkan aset SENA untuk klasifikasi kategori narasi dan NARA untuk pelabelan token beserta kode pembentuk field. Implementasi, data dan hasilnya berada di [models/slr09/](../../../models/slr09/README.md).

SENA menentukan kategori FLOOD, EARTHQUAKE, FIRE, ACCIDENT atau NON_EVENT. NARA dan adapter membentuk location_text, time_text, occurred_at, involved_parties, impacts, victims dan affected_objects. Nilai yang tidak dinyatakan tetap null atau array kosong. Label event NARA tidak mengganti kategori SENA.

Cutoff confidence 0,95; confidence di bawah cutoff ditandai rendah. NON_EVENT memblokir submission, verifikasi manusia selalu wajib, dan field kosong saja tidak membuat keluaran uncertain.

Training/pengujian aset selesai dan mutu pilot diterima menurut kriteria revisi pengguna. Rincian serta keterbatasannya tercatat pada [laporan FINAL084](../../../models/slr09/reports/README.md). Pemuatan di VM tujuan, penutupan formal card, integrasi aplikasi dan deployment mempunyai bukti/status tersendiri; penerimaan pilot tidak membuktikan kesiapan produksi.
