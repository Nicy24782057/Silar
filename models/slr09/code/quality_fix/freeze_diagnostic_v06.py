"""Freeze new assistant-proposed diagnostic before training/inference.

These labels are not human-approved acceptance references. This file is kept
separate from both the training generator and checkpoint-selection code.
"""
from pathlib import Path
from train_sena_cpu import write,sha
ROOT=Path(__file__).resolve().parents[2]

CASES={
'FLOOD':[
 ('plain','Banjir menerjang Dusun Sawangan tadi malam dan merendam belasan rumah.'),
 ('negated_simulation','Tolong jangan dikira gladi evakuasi. Banjir sedang merendam rumah kami di Gang Merica.'),
 ('victim_denial','Banjir menggenangi Perumahan Arunika, tetapi tidak ada korban jiwa menurut laporan posko.'),
 ('real_during_exercise','Peserta simulasi kebakaran harus keluar gedung karena banjir sungguhan masuk ke lantai dasar.'),
 ('clarified_reality','Warga mengira kabar itu lelucon. Petugas kemudian mengonfirmasi banjir nyata di Desa Walikukun.'),
 ('nonkeyword_effect','Tanggul jebol barusan; air sungai meluap melewati jendela rumah dan warga naik ke atap.'),
 ('alternative_denied','Tidak ada kebakaran di pasar. Yang terjadi adalah banjir, dengan air setinggi lutut para pedagang.'),
 ('future_negation','Banjir itu bukan prediksi untuk besok: hari ini air sudah menenggelamkan ruang kelas.'),
 ('negated_education','Ini bukan pertanyaan dalam buku pelajaran. Banjir baru saja memutus akses Kampung Randu.'),
 ('after_warning','Meski pengumuman awal hanya peringatan, banjir kini benar-benar terjadi dan menyeret dua gerobak.'),
],
'EARTHQUAKE':[
 ('plain','Gempa mengguncang Kabupaten Lembah Jernih pukul 03.15 dan meretakkan dinding beberapa rumah.'),
 ('negated_fiction','Jangan sebut cerita khayalan, gempa sungguhan baru mengguncang rumah kami sampai lemari terjatuh.'),
 ('victim_denial','Gempa merobohkan pagar balai warga pagi tadi. Syukurlah tidak ada orang yang terluka.'),
 ('real_during_exercise','Praktik berlindung di bawah meja terhenti ketika gempa asli mengguncang sekolah dan memecahkan kaca.'),
 ('aftershock_negation','Gempa terjadi pukul dua tadi; setelah itu tidak ada gempa susulan hingga laporan ini dikirim.'),
 ('nonkeyword_effect','Tanah berguncang kuat, lampu bergoyang, dan dinding rumah retak; warga sekampung keluar ke jalan.'),
 ('alternative_denied','Bukan kecelakaan kendaraan yang membuat warga keluar. Gempa sedang mengguncang kawasan perumahan.'),
 ('negated_education','Tidak sedang membicarakan teori. Gempa betulan baru terjadi di Desa Sumberjati dan atap balai rusak.'),
 ('rumor_verified','Kabar gempa awalnya diragukan, tetapi tim lapangan memastikan guncangan nyata dan menemukan rumah rusak.'),
 ('negated_simulation','Peringatan ini bukan bagian simulasi: gempa baru terasa keras di gedung kantor dan para pegawai berlarian.'),
],
'FIRE':[
 ('plain','Kebakaran melalap gudang kain di Jalan Seruni sore ini dan petugas sedang menyemprotkan air.'),
 ('negated_simulation','Jangan menganggap peragaan pemadam. Dapur kantin benar-benar kebakaran dan api menjalar ke atap.'),
 ('victim_denial','Kebakaran menghanguskan satu kios di Pasar Lazuardi tanpa menimbulkan korban luka.'),
 ('real_during_exercise','Pelatihan antigempa dihentikan karena kebakaran asli muncul di gudang bahan bakar sebelah lokasi.'),
 ('negated_fiction','Kebakaran yang sedang kami laporkan bukan adegan film. Dua rumah terbakar dan warga membutuhkan pemadam.'),
 ('nonkeyword_effect','Api menyambar atap rumah kontrakan, asap mengepul tebal, dan penghuni bergegas keluar meminta bantuan.'),
 ('alternative_denied','Bukan banjir di pabrik itu; kebakaran sedang berlangsung dan asap hitam terlihat dari jalan besar.'),
 ('forecast_versus_actual','Peringatan risiko kemarin kini menjadi kejadian: kebakaran terjadi di lereng bukit dan petugas memadamkan api.'),
 ('negated_education','Ini bukan latihan soal keselamatan. Bengkel di depan rumah saya kebakaran sejak beberapa menit lalu.'),
 ('location_negation','Kebakaran bukan di sekolah seperti kabar awal, melainkan di gudang sebelahnya; petugas sudah tiba.'),
],
'ACCIDENT':[
 ('plain','Kecelakaan terjadi di simpang Jalan Tanjung; sepeda motor menabrak sedan dan satu orang terluka.'),
 ('negated_simulation','Ini bukan demonstrasi cara berkendara. Bus menabrak pembatas di depan terminal dan penumpangnya cedera.'),
 ('victim_denial','Kecelakaan dua mobil di Jalan Bambu tidak menimbulkan korban jiwa, tetapi kedua kendaraan rusak.'),
 ('real_during_exercise','Latihan pengaturan jalan terhenti setelah sebuah motor sungguhan menabrak peserta di pintu masuk.'),
 ('negated_fiction','Tabrakan di depan bioskop bukan adegan syuting. Pengendara motor menabrak pejalan kaki dan ambulans dipanggil.'),
 ('nonkeyword_effect','Truk oleng lalu menghantam warung di tikungan; sopir terjepit dan tim penolong berusaha mengeluarkannya.'),
 ('alternative_denied','Tidak ada gempa di jembatan itu. Sebuah kecelakaan baru terjadi ketika dua truk bertabrakan.'),
 ('source_correction','Kabar kecelakaan semula dibantah, tetapi polisi di lokasi kemudian mengonfirmasi tabrakan dan dua korban luka.'),
 ('negated_education','Bukan soal ujian mengemudi: barusan mobil menabrak pagar sekolah dan pengemudinya terluka.'),
 ('negation_scope','Motor pertama tidak menabrak siapa pun, tetapi mobil di belakangnya menabrak pohon hingga penumpangnya terluka.'),
],
'NON_EVENT':[
 ('denial','Pengecekan polisi memastikan kabar kecelakaan di Jalan Melati keliru; mobil-mobil sedang parkir dan tidak ada tabrakan.'),
 ('denial','Kabar kebakaran kantor dibantah oleh pengelola; tidak ada api dan peristiwa tersebut tidak terjadi.'),
 ('education','Guru meminta murid menjelaskan penyebab gempa melalui gambar di papan tulis. Tidak ada peristiwa gempa yang dilaporkan.'),
 ('forecast','Peta perkiraan menandai potensi banjir pekan depan. Warga diminta menyiapkan perlengkapan sebelum ada kejadian.'),
 ('fiction','Pemain film merekam tabrakan menggunakan kendaraan mainan; adegan kecelakaan itu sepenuhnya rekaan.'),
 ('simulation','Panitia menggelar simulasi kebakaran dengan api tiruan dan pemeran korban. Semua peserta aman, tanpa kejadian sungguhan.'),
 ('hypothetical','Bagaimana bila gempa merobohkan rumah? Kalimat ini hanya ilustrasi dalam modul pelatihan.'),
 ('aggregate','Rapat mengevaluasi jumlah kecelakaan selama lima tahun sebagai statistik umum, tanpa laporan peristiwa tertentu.'),
 ('metaphor','Penyiar bercanda bahwa akun sang juara kebanjiran ucapan selamat; ia tidak sedang memberitakan bencana.'),
 ('planning','Bukan penanganan banjir yang sudah terjadi. Undangan ini hanya menjadwalkan latihan evakuasi untuk bulan depan.'),
]}


def freeze():
    rows=[{'id':f'NEW06-{label}-{i:02d}','text':text,'gold_label':label,'family':family,
           'reference_source':'ASSISTANT_AUTHORED_NOT_HUMAN_REVIEWED'}
          for label,items in CASES.items() for i,(family,text) in enumerate(items,1)]
    assert len(rows)==50 and all(len(items)==10 for items in CASES.values())
    path=ROOT/'data/frozen_new_diagnostic_v0.6.json'
    if path.exists():raise ValueError('Diagnostic already frozen; do not overwrite')
    write(path,{'schema':'slr09-new-diagnostic-0.6','status':'ASSISTANT_PROPOSED_REFERENCE_NOT_HUMAN_ACCEPTED',
                'frozen_before_training':True,'used_for_training_or_checkpoint_selection':False,'records':rows})
    print('Frozen new 50-case diagnostic SHA256:',sha(path),flush=True)


if __name__=='__main__':freeze()
