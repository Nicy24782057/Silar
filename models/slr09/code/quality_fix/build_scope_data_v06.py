"""Assistant-authored contrastive training and development; never human gold.

Train and development use different sentence templates. The separate manually
authored 50-case diagnostic is not read here and never used for model selection.
"""
import json
from pathlib import Path
from train_sena_cpu import write, sha

ROOT=Path(__file__).resolve().parents[2]
EVENTS={
 'FLOOD':('banjir','kebakaran','air sungai meluap dan merendam rumah penduduk'),
 'EARTHQUAKE':('gempa','kecelakaan','tanah bergetar keras dan dinding beberapa bangunan retak'),
 'FIRE':('kebakaran','banjir','api membakar atap gudang dan asap pekat membubung'),
 'ACCIDENT':('kecelakaan','gempa','sebuah mobil menabrak pohon dan pengemudinya terluka'),
}


def pairs(event,other,effect,place,time,development=False):
    if not development:
        return [
          ('negated_simulation',f'Ini bukan simulasi. {event.capitalize()} terjadi di {place} {time}; {effect}.',
           f'Ini hanya simulasi {event} di {place} {time}. Bukan kejadian sungguhan, dan tidak ada kerusakan nyata.'),
          ('negated_fiction',f'Laporan dari {place} {time} bukan cerita rekaan: {effect}. Petugas sedang menangani {event} tersebut.',
           f'Cerita rekaan tentang {event} di {place} dibacakan {time}. Bukan laporan peristiwa nyata.'),
          ('denied_victim',f'{event.capitalize()} melanda {place} {time}; {effect}. Tidak ada korban meninggal.',
           f'Tidak ada {event} di {place} {time}, tidak ada kerusakan, dan tidak ada korban; petugas membantah kabar tersebut.'),
          ('during_exercise',f'Latihan menghadapi {other} di {place} dihentikan {time} setelah {effect}. Itu {event} nyata, bukan bagian latihan.',
           f'Latihan menghadapi {event} di {place} {time} berjalan aman. Semua korban dan kerusakan merupakan bagian skenario, tidak ada kejadian nyata.'),
          ('other_type_denied',f'Tidak terjadi {other} di {place}. Yang terjadi {time} adalah {event}; {effect}.',
           f'Tidak terjadi {event} ataupun {other} di {place} {time}. Informasi yang beredar sudah diklarifikasi sebagai kabar keliru.'),
          ('beyond_lesson',f'Kegiatan belajar di {place} terhenti {time}: {effect}. Ini bukan materi pelajaran, melainkan {event} yang sedang ditangani.',
           f'Pelajaran di {place} {time} membahas {event} dan contoh kerusakan. Ini bukan laporan kejadian tertentu.'),
          ('source_correction',f'Awalnya kabar di {place} disangka latihan. Pemeriksaan {time} mengonfirmasi {effect}; petugas menyatakan kejadian itu nyata.',
           f'Awalnya beredar kabar {event} di {place}. Pemeriksaan {time} menyatakan kabar itu tidak benar dan peristiwa tersebut tidak berlangsung.'),
          ('negated_location',f'Bukan di pusat kota. Di {place}, {effect} {time}. Tim penolong sudah menuju kejadian tersebut.',
           f'Bukan laporan kejadian di {place}. Materi {time} hanya menjelaskan risiko {event} secara umum; tidak ada peristiwa yang sedang dilaporkan.'),
          ('no_panicked_witness',f'Tidak perlu panik, tetapi laporan dari {place} {time} menyebut {effect}. Petugas telah datang menangani keadaan.',
           f'Pesan pencegahan {event} di {place} {time} mengingatkan warga agar tidak panik. Tidak ada kejadian yang dilaporkan; ini hanya imbauan.'),
          ('forecast_versus_actual',f'Peringatan sebelumnya bukan sekadar dugaan lagi: {effect} di {place} {time}. Kejadian itu sedang berlangsung.',
           f'Di {place} {time}, petugas membahas kemungkinan {event} untuk waktu mendatang. Kejadian tersebut belum terjadi dan belum ada dampak nyata.'),
        ]
    return [
       ('dev_reality_correction',f'Jangan dianggap adegan buatan: {effect} di {place} {time}. Bantuan untuk peristiwa nyata sudah dikirim.',
        f'Kabar {event} yang dikaitkan dengan {place} {time} ternyata adegan buatan. Pengelola menegaskan tidak ada kejadian asli.'),
       ('dev_education_scope',f'Bukan pertanyaan ujian, ini laporan langsung dari {place}: {event} baru terjadi {time} dan warga memerlukan penanganan.',
        f'Pertanyaan ujian {time} meminta siswa membayangkan {event} di {place}. Kalimat itu tidak merujuk kejadian sungguhan.'),
       ('dev_drill_interrupted',f'Walaupun lokasi dipakai berlatih menghadapi {other}, laporan {time} dari {place} menyatakan {effect} di luar rencana latihan.',
        f'Di {place}, laporan latihan {time} memakai skenario {event}. Kerusakan yang disebutkan hanya properti latihan dan semua peserta aman.'),
       ('dev_negation_target',f'Tidak ada korban jiwa dalam {event} di {place} {time}, tetapi {effect}. Tim tanggap sedang bekerja.',
        f'Pemeriksaan {time} di {place} memastikan {event} tidak terjadi. Kalimat tentang korban hanyalah rumor yang dibantah.'),
       ('dev_suppressed_alternative',f'Petugas menyebut bukan {other} penyebab keadaan di {place} {time}. Terjadi {event}, dan {effect}.',
        f'Petugas di {place} {time} tidak melaporkan {event}; mereka hanya menerangkan prosedur penanganannya sebagai persiapan.'),
       ('dev_multiple_sentences',f'Berhenti menyebutnya lelucon. Di {place} {time}, {effect}. Warga sudah meminta pertolongan.',
        f'Lelucon tentang {event} di {place} dibicarakan {time}; penulisnya menjelaskan bahwa tidak ada peristiwa nyata yang dimaksud.'),
       ('dev_rumor_verified',f'Dugaan bahwa video itu hanya simulasi dibantah. Peninjauan di {place} {time} menemukan {effect}, sehingga kejadian dikonfirmasi nyata.',
        f'Video yang disebut {event} di {place} diperiksa {time}. Rekaman itu hanya simulasi; peristiwa nyata tidak terjadi.'),
       ('dev_time_scope',f'{event.capitalize()} bukan terjadi minggu depan. Di {place}, {effect} {time} dan petugas sudah menanganinya.',
        f'Pembahasan {time} di {place} mengenai persiapan menghadapi {event} minggu depan. Ini bukan laporan peristiwa yang sudah terjadi.'),
    ]


def build():
    result={}
    for name,development,places,times in [
       ('training',False,['Kelurahan Cendana','Desa Margahayu','Kampung Jatibening','kawasan Bukit Asri','Desa Kalirejo','kompleks Puspa Indah'],['tadi subuh','siang ini','kemarin malam','pukul tujuh','pagi tadi','sore ini']),
       ('development',True,['Desa Wanasari','Kelurahan Gadingrejo'],['barusan','tengah malam tadi'])]:
        rows=[]
        for label,(event,other,effect) in EVENTS.items():
            for index,(place,time) in enumerate(zip(places,times)):
                for family,positive,negative in pairs(event,other,effect,place,time,development):
                    for suffix,text,category in [('P',positive,label),('N',negative,'NON_EVENT')]:
                        rows.append({'id':f'SCOPE06-{name}-{label}-{family}-{index}-{suffix}',
                                     'text':text,'final':category,'family':family,
                                     'source':'ASSISTANT_AUTHORED_NOT_HUMAN_REVIEWED',
                                     'purpose':name,'review':{'status':'PENDING','reviewer':None}})
        result[name]=rows
        write(ROOT/f'data/scope_v06_{name}.json',{'schema':'slr09-scope-auxiliary-0.6',
              'human_reference':False,'records':rows})
    train={' '.join(x['text'].casefold().split()) for x in result['training']}
    dev={' '.join(x['text'].casefold().split()) for x in result['development']}
    assert len(train)==len(result['training']) and len(dev)==len(result['development']) and not train&dev
    write(ROOT/'data/scope_v06_data_identity.json',{
      'training_records':len(train),'assistant_development_records':len(dev),
      'source_code_sha256':sha(Path(__file__)),'files_sha256':{name:sha(ROOT/f'data/scope_v06_{name}.json') for name in ('training','development')},
      'template_families_disjoint_between_training_and_development':True,
      'human_review_of_new_examples_completed':False})
    print(json.dumps({'training_auxiliary':len(train),'assistant_development':len(dev),'human_review_completed':False}),flush=True)


if __name__=='__main__':build()
