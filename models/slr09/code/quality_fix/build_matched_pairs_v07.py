"""Matched wording with different factual scope; assistant labels remain proposals."""
from pathlib import Path
import json
from train_sena_cpu import write,sha
ROOT=Path(__file__).resolve().parents[2]
EFFECTS={
 'FLOOD':[
 'banjir menggenangi jalan sampai setinggi lutut','air sungai meluap dan masuk ke rumah warga',
 'banjir bandang menyeret gerobak pedagang','tanggul jebol sehingga permukiman terendam',
 'banjir rob merendam ruang kelas','arus banjir memutus akses jembatan',
 'banjir merusak kios dan menghanyutkan barang','air meluber dari sungai dan warga mengungsi akibat banjir'],
 'EARTHQUAKE':[
 'gempa merobohkan tembok rumah','guncangan gempa memecahkan kaca sekolah',
 'gempa membuat pegawai berlari keluar kantor','tanah berguncang karena gempa dan plafon berjatuhan',
 'gempa meretakkan dinding balai warga','getaran gempa menggoyangkan lemari dan menjatuhkan lampu',
 'gempa merusak atap pos ronda','gempa terasa kuat sehingga warga menjauh dari bangunan'],
 'FIRE':[
 'kebakaran melalap gudang pakaian','api menyambar atap rumah dan asap mengepul',
 'kebakaran merusak bengkel kendaraan','kobaran api menjalar dari dapur ke ruang tamu',
 'kebakaran menghanguskan dua kios','api membakar kandang dan petugas memadamkannya',
 'kebakaran terjadi di kantin sehingga siswa dievakuasi','nyala api membesar di toko akibat kebakaran'],
 'ACCIDENT':[
 'sebuah motor menabrak pejalan kaki','kecelakaan dua mobil merusak pagar toko',
 'truk menyerempet sepeda motor dan pengendaranya cedera','bus menabrak pohon di tepi jalan',
 'minibus terguling dalam kecelakaan di tikungan','dua sepeda motor bertabrakan di persimpangan',
 'sedan menabrak pembatas jalan hingga pengemudinya terluka','kecelakaan angkot membuat dua penumpang terjepit']}
PLACES=['Desa Karangsari','Kelurahan Nusaputih','Kampung Cemara','Desa Purwajaya','kawasan Sukatani','Kelurahan Harumjaya','Desa Mekarjati','kompleks Pringasri']
OTHER={'FLOOD':'kebakaran','EARTHQUAKE':'kecelakaan','FIRE':'banjir','ACCIDENT':'gempa'}


def build():
    rows=[]
    for label,effects in EFFECTS.items():
        for i,effect in enumerate(effects):
            p=PLACES[i];other=OTHER[label]
            versions=[
              (f'Ini bukan bagian latihan: {effect} di {p} barusan. Tim lapangan memastikan peristiwa asli.',
               f'Ini bagian latihan: kalimat "{effect} di {p}" hanya skenario dengan pemain, bukan kejadian asli.'),
              (f'Petugas tidak sedang menceritakan dongeng. Faktanya, {effect} di {p} dan bantuan sudah tiba.',
               f'Kalimat "{effect} di {p}" ada dalam dongeng rekaan. Tidak ada peristiwa sungguhan yang dilaporkan.'),
              (f'{other.capitalize()} tidak terjadi di {p}. Yang benar, {effect} hari ini menurut pemeriksaan petugas.',
               f'Informasi "{effect} di {p}" tidak benar. Petugas memeriksa lokasi dan memastikan kejadian itu tidak terjadi.'),
              (f'{effect.capitalize()} di {p} tadi pagi. Setelah itu tidak ada kejadian susulan, tetapi peristiwa awal memang terjadi.',
               f'Kalimat "{effect} di {p}" hanya perkiraan risiko untuk bulan depan. Sampai sekarang kejadian itu belum berlangsung.'),
              (f'Bukan di sekolah seperti rumor awal. Sebenarnya {effect} di {p} dan petugas sudah menanganinya.',
               f'Rumor bahwa "{effect} di {p}" sudah diklarifikasi. Tidak ada kejadian itu, dan lokasi dinyatakan aman.'),
              (f'Rumor bahwa laporan itu cuma rekayasa telah dibantah. Petugas mengonfirmasi {effect} di {p} sebagai kejadian nyata.',
               f'Rumor "{effect} di {p}" telah dibantah. Yang terlihat hanya properti peragaan dan tidak ada peristiwa nyata.'),
              (f'{effect.capitalize()} di {p}, tanpa korban meninggal. Kerusakan akibat kejadian tersebut masih ditangani.',
               f'Kalimat "{effect} di {p}" dan keterangan korban hanyalah dialog adegan fiksi; semua kerusakan merupakan properti.'),
              (f'Rencana latihan di {p} dihentikan karena {effect}. Ini peristiwa di luar skenario dan petugas meminta bantuan.',
               f'Rencana latihan di {p} minggu depan memakai skenario "{effect}". Ini undangan kegiatan, bukan laporan kejadian.')]
            for family,(positive,negative) in enumerate(versions):
                pair=f'PAIR07-{label}-{i}-{family}'
                for pol,text,final in [('P',positive,label),('N',negative,'NON_EVENT')]:
                    rows.append({'id':pair+'-'+pol,'pair_id':pair,'pair_category':label,'polarity':pol,
                                 'text':text,'final':final,'source':'ASSISTANT_MATCHED_PAIR_NOT_HUMAN_GOLD',
                                 'review':{'status':'PENDING','reviewer':None}})
    write(ROOT/'data/matched_pairs_v07_training.json',{'schema':'slr09-matched-pairs-0.7','human_reference':False,'records':rows})
    old=json.loads((ROOT/'data/quality_fix_fresh_challenge_v0.5.json').read_text())['records']
    seen=json.loads((ROOT/'data/frozen_new_diagnostic_v0.6.json').read_text())['records']
    dev=[dict(r,final=r['gold_label'],source='RETIRED_ASSISTANT_DIAGNOSTIC_NOW_DEVELOPMENT_NOT_HUMAN_GOLD') for r in old+seen]
    write(ROOT/'data/mvp_seen_development_v07.json',{'schema':'slr09-mvp-development-0.7','status':'ASSISTANT_PROPOSED_REFERENCE_NOT_HUMAN_ACCEPTED','records':dev})
    write(ROOT/'data/diagnostic_retirement_v07.json',{'old24_and_v06_new50_now_development':True,
          'reason':'Failures and intercept ablation have been inspected; these sets must not be presented as unseen acceptance again.',
          'new_human_review_completed':False,'training_pairs_sha256':sha(ROOT/'data/matched_pairs_v07_training.json')})
    print('Matched pair training records:',len(rows),'Retired diagnostic development:',len(dev),flush=True)


if __name__=='__main__':build()
