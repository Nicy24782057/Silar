"""Prospective class diagnostic, frozen before v0.7 fitting; not human gold."""
import json
from pathlib import Path
from datetime import datetime, timezone
from train_sena_cpu import write, sha
ROOT=Path(__file__).resolve().parents[2]
CASES={
 'FLOOD':[
  ('plain','Air banjir sudah setinggi pinggang di Gang Kelor sejak pukul enam dan keluarga kami mengungsi ke masjid.'),
  ('plain','Hujan deras membuat Sungai Tawar meluap pagi ini; aliran air menggenangi puluhan rumah di bantaran.'),
  ('victim_negation','Tidak seorang pun meninggal, meskipun banjir tadi malam menghancurkan tiga rumah di Dusun Papar.'),
  ('exercise_contrast','Petugas sedang berlatih menolong korban gempa ketika air banjir betulan menerobos tempat latihan dan mereka harus pindah.'),
  ('rumor_verified','Foto permukiman terendam itu sempat disebut palsu. Relawan di lokasi memastikan banjir benar terjadi dan membawa warga keluar.'),
  ('local_negation','Rumah di bukit tidak kebanjiran, tetapi rumah kami di bantaran sungai sudah terendam dan kami menunggu perahu.'),
  ('nonkeyword','Tanggul di belakang pasar runtuh sore ini. Air sungai masuk ke deretan toko hingga dagangan hanyut dan pedagang mengungsi.'),
  ('not_future','Yang dilaporkan bukan kemungkinan pekan depan. Banjir sudah masuk ke puskesmas hari ini dan pasien dipindahkan.'),
  ('other_event_denied','Kabar gempa di kampung kami salah. Justru banjir yang sedang terjadi, dengan jalan dan halaman rumah tergenang.'),
  ('fiction_denied','Gambar banjir di layar ini bukan cuplikan sinetron; siaran langsung memperlihatkan petugas mengevakuasi warga dari rumah terendam.'),
 ],
 'EARTHQUAKE':[
  ('plain','Gempa terasa kuat di Kecamatan Tegalreja siang ini, membuat warga keluar dan menyebabkan tembok toko retak.'),
  ('plain','Guncangan gempa menjatuhkan genting balai desa pukul 04.20; petugas masih memeriksa bangunan.'),
  ('victim_negation','Tidak ditemukan korban cedera setelah gempa mengguncang Desa Manggala dan merusak dinding dua sekolah.'),
  ('exercise_contrast','Latihan menghadapi banjir mendadak berhenti. Tanah benar-benar berguncang akibat gempa dan peserta keluar dari gedung.'),
  ('rumor_verified','Pengumuman pertama dianggap gurauan, lalu seismolog dan warga membenarkan gempa baru terjadi serta merusak pagar rumah.'),
  ('local_negation','Laporan ini bukan tentang gempa susulan. Gempa awal pukul satu tadi telah merobohkan atap sebuah rumah.'),
  ('nonkeyword','Lantai bergetar hebat, lampu gantung bergoyang dan dinding retak bersamaan di seluruh kampung. Badan geofisika mengonfirmasi guncangan tektonik.'),
  ('not_future','Petugas tidak sedang meramalkan gempa. Mereka melaporkan gempa yang baru saja mengguncang kota dan memecahkan kaca kantor.'),
  ('other_event_denied','Bunyi keras itu bukan tabrakan di jalan. Gempa sedang mengguncang gedung kami hingga plafonnya jatuh.'),
  ('fiction_denied','Kami tidak sedang menonton efek film. Gempa sungguhan menggoyang studio dan seluruh kru berlari ke halaman.'),
 ],
 'FIRE':[
  ('plain','Warung di samping bengkel Jalan Pulasan kebakaran pagi ini; kobaran api merambat ke dua atap di sebelahnya.'),
  ('plain','Api membakar ruang penyimpanan pasar sejak tadi malam dan tiga mobil pemadam masih berusaha memadamkannya.'),
  ('victim_negation','Kebakaran menghanguskan kandang di Desa Sidamukti, tetapi seluruh pekerja selamat dan tidak ada korban luka.'),
  ('exercise_contrast','Saat warga mengikuti simulasi evakuasi banjir, tabung di kantin bocor dan kebakaran nyata terjadi di dapur.'),
  ('rumor_verified','Pemilik semula menyangka pesan itu lelucon. Setelah mengecek, ia memastikan tokonya benar-benar terbakar dan meminta pemadam.'),
  ('local_negation','Bukan gudang kayu yang terbakar. Kebakaran terjadi di rumah sebelahnya dan petugas sedang menyemprot ruang tamu.'),
  ('nonkeyword','Asap pekat keluar dari rumah kosong, disusul nyala api yang melahap kusen dan atap; warga memanggil pemadam.'),
  ('not_future','Risiko yang diperingatkan kemarin sudah menjadi peristiwa: api kini membakar bukit di belakang kampung dan petugas memadamkannya.'),
  ('other_event_denied','Tidak ada banjir di pusat perbelanjaan itu. Yang terjadi kebakaran di lantai dua, dengan asap tebal dan pengunjung dievakuasi.'),
  ('fiction_denied','Video ini tidak memakai api buatan. Kebakaran di garasi benar terjadi dan mobil di dalamnya hangus.'),
 ],
 'ACCIDENT':[
  ('plain','Dua sepeda motor bertabrakan di jembatan Jalan Selada tadi sore; seorang pengendara dibawa ke rumah sakit.'),
  ('plain','Mobil bak terbuka menabrak tiang dekat terminal pagi ini sehingga pengemudinya terjepit di kabin.'),
  ('victim_negation','Tidak ada korban jiwa dalam kecelakaan bus dan truk di Jalan Kecapi, meskipun bagian depan bus rusak berat.'),
  ('exercise_contrast','Praktik penyeberangan sekolah dihentikan setelah motor sungguhan menabrak pagar dan pengendaranya terluka.'),
  ('rumor_verified','Laporan tabrakan sempat dianggap bohong. Polisi yang tiba kemudian menemukan dua kendaraan rusak dan menolong penumpang cedera.'),
  ('local_negation','Sopir membantah menabrak pejalan kaki, tetapi mengakui mobilnya menabrak pohon dan dua penumpangnya terluka.'),
  ('nonkeyword','Truk kehilangan kendali lalu menghantam gerobak di persimpangan; pedagang terjatuh dan ambulans menjemputnya.'),
  ('not_future','Ini bukan contoh dalam buku mengemudi. Sebuah angkot baru saja terguling di tikungan dan penumpangnya meminta pertolongan.'),
  ('other_event_denied','Tidak ada kebakaran di ruas tol itu. Kecelakaan baru terjadi ketika sedan menabrak belakang bus.'),
  ('fiction_denied','Adegan di depan lokasi syuting itu ternyata bukan bagian film: motor menabrak pesepeda dan kru memanggil ambulans.'),
 ],
 'NON_EVENT':[
  ('denial','Petugas memastikan informasi rumah terbakar di Gang Nanas adalah kabar palsu. Pemeriksaan tidak menemukan api maupun bangunan terbakar.'),
  ('denial','Rekaman yang disebut tabrakan di terminal ternyata kendaraan sedang diparkir. Polisi menyatakan kecelakaan itu tidak pernah terjadi.'),
  ('education','Dalam kelas geografi, murid membaca kalimat tentang gempa merobohkan tembok sebagai contoh. Guru tidak melaporkan kejadian nyata.'),
  ('forecast','Peringatan cuaca menyebut sungai berpotensi meluap akhir pekan nanti. Hingga pengumuman ini dibuat, belum ada banjir yang terjadi.'),
  ('fiction','Novel yang sedang dibahas berkisah tentang kota terbakar dan penduduk mengungsi. Seluruh peristiwa dan kotanya rekaan penulis.'),
  ('simulation','Suara benturan dalam latihan kecelakaan berasal dari pengeras suara. Mobil rusak dan korban merupakan properti serta pemeran simulasi.'),
  ('hypothetical','Jika gempa terjadi saat rapat, ke mana peserta harus berkumpul? Panitia hanya meminta usulan prosedur darurat.'),
  ('aggregate','Tabel tahunan membandingkan angka kebakaran selama sepuluh tahun. Tidak ada laporan kejadian kebakaran tertentu dalam pesan ini.'),
  ('metaphor','Toko daring itu kebanjiran pesanan setelah promosi; istilah itu menggambarkan banyaknya pembeli, tanpa adanya genangan air.'),
  ('planning','Undangan bulan depan mencantumkan skenario banjir merendam pasar. Acara belum berlangsung dan skenario tersebut bukan laporan peristiwa nyata.'),
 ]}

def freeze():
    rows=[{'id':f'NEW07-{label}-{i:02d}','text':text,'gold_label':label,'family':family,
           'reference_source':'ASSISTANT_AUTHORED_NOT_HUMAN_REVIEWED'}
          for label,items in CASES.items() for i,(family,text) in enumerate(items,1)]
    assert len(rows)==50 and all(len(v)==10 for v in CASES.values())
    normal=lambda s:' '.join(s.casefold().split())
    sources=[]
    for name in ('matched_pairs_v07_training.json','mvp_seen_development_v07.json'):
        sources+=json.loads((ROOT/'data'/name).read_text())['records']
    for part in ('train','validation'):
        sources += [json.loads(s) for s in (ROOT/f'data/sena_{part}_reviewed.jsonl').read_text().splitlines() if s.strip()]
    sources+=json.loads((ROOT/'evidence/quality_fix_v05/previous_50/reviewed_bundle_frozen.json').read_text())['records']
    sources+=json.loads((ROOT/'evidence/quality_fix_v05/training_run_20261019_cpu/training_auxiliary.json').read_text())
    assert len({normal(r['text']) for r in rows})==50
    assert not {normal(r['text']) for r in rows}&{normal(r['text']) for r in sources}
    path=ROOT/'data/frozen_new_diagnostic_v0.7.json'
    if path.exists():raise ValueError('Already frozen; do not overwrite')
    write(path,{'schema':'slr09-new-diagnostic-0.7','status':'ASSISTANT_PROPOSED_REFERENCE_NOT_HUMAN_ACCEPTED',
        'frozen_at':datetime.now(timezone.utc).isoformat(),'frozen_before_training':True,
        'used_for_training_or_checkpoint_selection':False,'records':rows})
    write(ROOT/'data/scope_v07_split_guard.json',{'new50_sha256':sha(path),
        'normalized_exact_overlap_count':0,'comparison_records':len(sources),
        'semantic_or_template_independence_established':False,'human_reference_reviewed':False,
        'frozen_before_training':True})
    print('Frozen prospective v0.7 SHA256:',sha(path))

if __name__=='__main__':freeze()
