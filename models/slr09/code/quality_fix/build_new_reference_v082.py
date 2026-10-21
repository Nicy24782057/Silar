"""New, varied synthetic proposals. No model imports or inference; all PENDING."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/acceptance'))
from evaluate_acceptance import token_items,ROLES,validate_fields,write,normal


def build():
    out=ROOT/'data/final_reference_proposals_v0.8.2.json'
    if out.exists():raise ValueError('Do not overwrite a frozen proposal file')
    rows=[]
    def add(label,family,marked,location=None,time=None,parties=(),impacts=(),victims=(),objects=()):
        text='';spans=[];end=0
        for match in re.finditer(r'\{([A-Z-]+):([^}]+)\}',marked):
            text+=marked[end:match.start()];start=len(text);text+=match[2]
            spans.append((start,len(text),match[1]));end=match.end()
        text+=marked[end:]
        labels=[next((role for a,b,role in spans if a<=t.start() and t.end()<=b),'O') for t in token_items(text)]
        fields={'location_text':location,'time_text':time,'occurred_at':None,'involved_parties':list(parties),
            'impacts':list(impacts),'victims':list(victims),'affected_objects':list(objects)}
        validate_fields(fields,text);assert set(labels)<=set(ROLES)
        index=1+sum(r['gold_label']==label for r in rows)
        rows.append({'id':f'FINAL082-{label}-{index:02d}','text':text,'family':family,
            'gold_label':label,'gold_fields':fields,'gold_nara_labels':labels,
            'origin':{'kind':'ASSISTANT_AUTHORED_SYNTHETIC','reference':'New v0.8.2 proposal, varied narrative constructions; no model predictions inspected; not a field report.'},
            'review':{'status':'PENDING','reviewer':'','at':'','note':''}})

    add('FLOOD','plain','{OFFICER-ARG:Relawan} melaporkan {FLOOD-EVENT:banjir} yang {INFORMATION-ARG:merendam} {AFFECTEDOBJECTS-ARG:dua warung} di {PLACE-ARG:Kelurahan Suramerta} {TIME-ARG:siang ini}.',
        'Kelurahan Suramerta','siang ini',['Relawan'],['merendam dua warung'],objects=['dua warung'])
    add('FLOOD','object_first','{AFFECTEDOBJECTS-ARG:Satu sekolah} {INFORMATION-ARG:terendam} {FLOOD-EVENT:banjir} di {PLACE-ARG:Desa Pangkalreja} {TIME-ARG:sejak pagi}.',
        'Desa Pangkalreja','sejak pagi',impacts=['Satu sekolah terendam'],objects=['Satu sekolah'])
    add('FLOOD','cause','Akibat {REASON-ARG:tanggul jebol}, {FLOOD-EVENT:banjir} {INFORMATION-ARG:menutup} {AFFECTEDOBJECTS-ARG:jalan utama} di {PLACE-ARG:Kampung Selangwangi} {TIME-ARG:tadi malam}.',
        'Kampung Selangwangi','tadi malam',impacts=['menutup jalan utama'],objects=['jalan utama'])
    add('FLOOD','victim','{FLOOD-EVENT:Banjir} {INFORMATION-ARG:menggenangi} {AFFECTEDOBJECTS-ARG:empat rumah} di {PLACE-ARG:Desa Pakuindah} {TIME-ARG:pagi tadi}; {WOUNDVICTIM-ARG:dua warga terluka}.',
        'Desa Pakuindah','pagi tadi',['dua warga'],['menggenangi empat rumah'],['dua warga terluka'],['empat rumah'])
    add('FLOOD','response','Di {PLACE-ARG:Kelurahan Bentengwangi}, {OFFICER-ARG:tim SAR} {INFORMATION-ARG:mengevakuasi warga} akibat {FLOOD-EVENT:banjir} {TIME-ARG:sore ini}.',
        'Kelurahan Bentengwangi','sore ini',['tim SAR'],['mengevakuasi warga'])
    add('FLOOD','local_negation','{FLOOD-EVENT:Banjir} {INFORMATION-ARG:merendam} {AFFECTEDOBJECTS-ARG:tiga kios} di {STREET-ARG:Jalan Mahadewi} {TIME-ARG:malam tadi}, tetapi tidak ada korban.',
        'Jalan Mahadewi','malam tadi',impacts=['merendam tiga kios'],objects=['tiga kios'])
    add('FLOOD','real_during_exercise','Saat latihan pertolongan, {FLOOD-EVENT:banjir} nyata {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:jembatan kayu} di {PLACE-ARG:Desa Bantarasih} {TIME-ARG:siang tadi}.',
        'Desa Bantarasih','siang tadi',impacts=['merusak jembatan kayu'],objects=['jembatan kayu'])
    add('FLOOD','rumor_verified','{OFFICER-ARG:Petugas desa} memastikan {FLOOD-EVENT:banjir} benar terjadi di {PLACE-ARG:Kampung Lembarsari} {TIME-ARG:kemarin sore}; {INFORMATION-ARG:air masuk} {AFFECTEDOBJECTS-ARG:dua toko}.',
        'Kampung Lembarsari','kemarin sore',['Petugas desa'],['air masuk dua toko'],objects=['dua toko'])
    add('FLOOD','death','{DEATHVICTIM-ARG:Seorang penjaga meninggal} setelah {FLOOD-EVENT:banjir} di {PLACE-ARG:Desa Cisaloka} {TIME-ARG:subuh tadi}.',
        'Desa Cisaloka','subuh tadi',['Seorang penjaga'],victims=['Seorang penjaga meninggal'])
    add('FLOOD','contrasted_location','{FLOOD-EVENT:Banjir} {INFORMATION-ARG:melanda} {PLACE-ARG:Kampung Panyawangan} {TIME-ARG:malam ini}. Wilayah di bukit tetap kering.',
        'Kampung Panyawangan','malam ini',impacts=['melanda Kampung Panyawangan'])

    add('EARTHQUAKE','plain','{TIME-ARG:Tadi pagi}, {EARTHQUAKE-EVENT:gempa} {INFORMATION-ARG:mengguncang} {PLACE-ARG:Kelurahan Batuwangi} dan {OFFICER-ARG:warga} {INFORMATION-ARG:berlarian keluar}.',
        'Kelurahan Batuwangi','Tadi pagi',['warga'],['mengguncang Kelurahan Batuwangi','berlarian keluar'])
    add('EARTHQUAKE','object_first','{AFFECTEDOBJECTS-ARG:Dinding balai desa} {INFORMATION-ARG:roboh} akibat {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Desa Kemuningasri} {TIME-ARG:siang ini}.',
        'Desa Kemuningasri','siang ini',impacts=['Dinding balai desa roboh'],objects=['Dinding balai desa'])
    add('EARTHQUAKE','victim','{EARTHQUAKE-EVENT:Gempa} di {PLACE-ARG:Kampung Sukalarang} {TIME-ARG:tadi malam} {INFORMATION-ARG:mengakibatkan} {WOUNDVICTIM-ARG:tiga warga terluka}.',
        'Kampung Sukalarang','tadi malam',['tiga warga'],['mengakibatkan tiga warga terluka'],victims=['tiga warga terluka'])
    add('EARTHQUAKE','cause','{REASON-ARG:Pergerakan sesar} memicu {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Desa Linggawana} {TIME-ARG:sore tadi}; {AFFECTEDOBJECTS-ARG:dua rumah} {INFORMATION-ARG:rusak}.',
        'Desa Linggawana','sore tadi',impacts=['dua rumah rusak'],objects=['dua rumah'])
    add('EARTHQUAKE','response','{OFFICER-ARG:Petugas BPBD} {INFORMATION-ARG:mengevakuasi warga} setelah {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Kelurahan Banjarwangi} {TIME-ARG:pagi ini}.',
        'Kelurahan Banjarwangi','pagi ini',['Petugas BPBD'],['mengevakuasi warga'])
    add('EARTHQUAKE','local_negation','Tak ada korban jiwa dalam {EARTHQUAKE-EVENT:gempa} {TIME-ARG:siang tadi} di {PLACE-ARG:Desa Cikawana}, tetapi {AFFECTEDOBJECTS-ARG:pagar sekolah} {INFORMATION-ARG:roboh}.',
        'Desa Cikawana','siang tadi',impacts=['pagar sekolah roboh'],objects=['pagar sekolah'])
    add('EARTHQUAKE','real_during_exercise','Latihan evakuasi dihentikan karena {EARTHQUAKE-EVENT:gempa} sungguhan {INFORMATION-ARG:mengguncang} {PLACE-ARG:Kampung Cendrawana} {TIME-ARG:sore ini}.',
        'Kampung Cendrawana','sore ini',impacts=['mengguncang Kampung Cendrawana'])
    add('EARTHQUAKE','death','{EARTHQUAKE-EVENT:Gempa} {INFORMATION-ARG:merobohkan} {AFFECTEDOBJECTS-ARG:satu warung} di {PLACE-ARG:Desa Pagelaras} {TIME-ARG:malam tadi}; {DEATHVICTIM-ARG:satu pedagang meninggal}.',
        'Desa Pagelaras','malam tadi',['satu pedagang'],['merobohkan satu warung'],['satu pedagang meninggal'],['satu warung'])
    add('EARTHQUAKE','rumor_verified','Video itu asli: {EARTHQUAKE-EVENT:gempa} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:atap sekolah} di {PLACE-ARG:Kelurahan Narawangi} {TIME-ARG:kemarin siang}.',
        'Kelurahan Narawangi','kemarin siang',impacts=['merusak atap sekolah'],objects=['atap sekolah'])
    add('EARTHQUAKE','ongoing','{EARTHQUAKE-EVENT:Gempa susulan} {INFORMATION-ARG:terasa kuat} di {PLACE-ARG:Desa Rancamurni} {TIME-ARG:malam ini}; {OFFICER-ARG:warga} {INFORMATION-ARG:mengungsi}.',
        'Desa Rancamurni','malam ini',['warga'],['terasa kuat','mengungsi'])

    add('FIRE','plain','{FIRE-EVENT:Api} {INFORMATION-ARG:menghanguskan} {AFFECTEDOBJECTS-ARG:dua kios} di {PLACE-ARG:Pasar Rengganis} {TIME-ARG:subuh tadi}.',
        'Pasar Rengganis','subuh tadi',impacts=['menghanguskan dua kios'],objects=['dua kios'])
    add('FIRE','cause','{FIRE-EVENT:Kebakaran} akibat {REASON-ARG:kompor bocor} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:dapur sekolah} di {PLACE-ARG:Desa Kertajaya} {TIME-ARG:siang tadi}.',
        'Desa Kertajaya','siang tadi',impacts=['merusak dapur sekolah'],objects=['dapur sekolah'])
    add('FIRE','victim','{FIRE-EVENT:Kebakaran} terjadi di {PLACE-ARG:Gudang Suryamurni} {TIME-ARG:malam tadi}; {WOUNDVICTIM-ARG:dua pekerja terluka}.',
        'Gudang Suryamurni','malam tadi',['dua pekerja'],victims=['dua pekerja terluka'])
    add('FIRE','response','{OFFICER-ARG:Petugas damkar} {INFORMATION-ARG:memadamkan} {FIRE-EVENT:kebakaran} di {STREET-ARG:Jalan Cempakareja} {TIME-ARG:pagi ini}.',
        'Jalan Cempakareja','pagi ini',['Petugas damkar'],['memadamkan kebakaran'])
    add('FIRE','object_first','{AFFECTEDOBJECTS-ARG:Satu rumah} {INFORMATION-ARG:hangus} dalam {FIRE-EVENT:kebakaran} di {PLACE-ARG:Kampung Tanjungasih} {TIME-ARG:sore tadi}.',
        'Kampung Tanjungasih','sore tadi',impacts=['Satu rumah hangus'],objects=['Satu rumah'])
    add('FIRE','local_negation','{FIRE-EVENT:Kebakaran} {INFORMATION-ARG:menghanguskan} {AFFECTEDOBJECTS-ARG:gudang kayu} di {PLACE-ARG:Desa Babakanasri} {TIME-ARG:kemarin malam}; tidak ada korban.',
        'Desa Babakanasri','kemarin malam',impacts=['menghanguskan gudang kayu'],objects=['gudang kayu'])
    add('FIRE','real_during_exercise','Di tengah latihan damkar, {FIRE-EVENT:kebakaran} nyata {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:satu mobil} di {PLACE-ARG:Lapangan Mekarjaya} {TIME-ARG:siang ini}.',
        'Lapangan Mekarjaya','siang ini',impacts=['merusak satu mobil'],objects=['satu mobil'])
    add('FIRE','death','{DEATHVICTIM-ARG:Seorang penjaga meninggal} dalam {FIRE-EVENT:kebakaran} di {PLACE-ARG:Kelurahan Citranagara} {TIME-ARG:dini hari}.',
        'Kelurahan Citranagara','dini hari',['Seorang penjaga'],victims=['Seorang penjaga meninggal'])
    add('FIRE','rumor_verified','{OFFICER-ARG:Warga} membantah kabar palsu itu: {FIRE-EVENT:kebakaran} benar-benar terjadi dan {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:kantor desa} di {PLACE-ARG:Desa Pasirmadu} {TIME-ARG:sore ini}.',
        'Desa Pasirmadu','sore ini',['Warga'],['merusak kantor desa'],objects=['kantor desa'])
    add('FIRE','cause','Karena {REASON-ARG:korsleting listrik}, {FIRE-EVENT:api} {INFORMATION-ARG:melalap} {AFFECTEDOBJECTS-ARG:satu toko} di {PLACE-ARG:Pasar Wanasari} {TIME-ARG:malam ini}.',
        'Pasar Wanasari','malam ini',impacts=['melalap satu toko'],objects=['satu toko'])

    add('ACCIDENT','plain','{ACCIDENT-EVENT:Kecelakaan} {INFORMATION-ARG:melibatkan} {AFFECTEDOBJECTS-ARG:dua motor} di {STREET-ARG:Jalan Sidomurni} {TIME-ARG:pagi ini}.',
        'Jalan Sidomurni','pagi ini',impacts=['melibatkan dua motor'],objects=['dua motor'])
    add('ACCIDENT','cause','Akibat {REASON-ARG:rem blong}, {ACCIDENT-EVENT:kecelakaan} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:satu bus} di {PLACE-ARG:Desa Lembahreja} {TIME-ARG:siang tadi}.',
        'Desa Lembahreja','siang tadi',impacts=['merusak satu bus'],objects=['satu bus'])
    add('ACCIDENT','victim','{ACCIDENT-EVENT:Kecelakaan} di {STREET-ARG:Jalan Angsana} {TIME-ARG:sore tadi} {INFORMATION-ARG:menyebabkan} {WOUNDVICTIM-ARG:dua penumpang terluka}.',
        'Jalan Angsana','sore tadi',['dua penumpang'],['menyebabkan dua penumpang terluka'],victims=['dua penumpang terluka'])
    add('ACCIDENT','response','{OFFICER-ARG:Polisi} {INFORMATION-ARG:mengevakuasi korban} setelah {ACCIDENT-EVENT:kecelakaan} di {PLACE-ARG:Kelurahan Tamanreja} {TIME-ARG:malam tadi}.',
        'Kelurahan Tamanreja','malam tadi',['Polisi'],['mengevakuasi korban'])
    add('ACCIDENT','death','{DEATHVICTIM-ARG:Satu pengendara meninggal} akibat {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Sukaluyu} {TIME-ARG:subuh tadi}.',
        'Jalan Sukaluyu','subuh tadi',['Satu pengendara'],victims=['Satu pengendara meninggal'])
    add('ACCIDENT','local_negation','Tidak ada korban luka dalam {ACCIDENT-EVENT:kecelakaan} di {PLACE-ARG:Desa Tegalwangi} {TIME-ARG:siang ini}, tetapi {AFFECTEDOBJECTS-ARG:dua mobil} {INFORMATION-ARG:rusak}.',
        'Desa Tegalwangi','siang ini',impacts=['dua mobil rusak'],objects=['dua mobil'])
    add('ACCIDENT','real_during_exercise','Saat latihan pertolongan, {ACCIDENT-EVENT:kecelakaan} sungguhan {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:mobil petugas} di {PLACE-ARG:Lapangan Binamarga} {TIME-ARG:sore ini}.',
        'Lapangan Binamarga','sore ini',impacts=['merusak mobil petugas'],objects=['mobil petugas'])
    add('ACCIDENT','object_first','{AFFECTEDOBJECTS-ARG:Truk pengangkut pasir} {INFORMATION-ARG:terguling} dalam {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Cadaswangi} {TIME-ARG:kemarin pagi}.',
        'Jalan Cadaswangi','kemarin pagi',impacts=['Truk pengangkut pasir terguling'],objects=['Truk pengangkut pasir'])
    add('ACCIDENT','rumor_verified','Rekaman itu bukan adegan film; {ACCIDENT-EVENT:kecelakaan} benar terjadi dan {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:satu angkot} di {PLACE-ARG:Kelurahan Mulyawana} {TIME-ARG:pagi tadi}.',
        'Kelurahan Mulyawana','pagi tadi',impacts=['merusak satu angkot'],objects=['satu angkot'])
    add('ACCIDENT','cause','{ACCIDENT-EVENT:Kecelakaan} dipicu {REASON-ARG:jalan licin} di {STREET-ARG:Jalan Cempakaluyu} {TIME-ARG:malam ini}; {WOUNDVICTIM-ARG:seorang sopir terluka}.',
        'Jalan Cempakaluyu','malam ini',['seorang sopir'],victims=['seorang sopir terluka'])

    add('NON_EVENT','simulation','{OFFICER-ARG:Tim damkar} hanya menggelar simulasi {FALSE-EVENT:kebakaran} di {PLACE-ARG:Halaman Purnawana} {TIME-ARG:pagi tadi}.',
        'Halaman Purnawana','pagi tadi',['Tim damkar'])
    add('NON_EVENT','exercise_only','{FALSE-EVENT:Kecelakaan} dalam latihan di {PLACE-ARG:Balai Suryalaya} {TIME-ARG:sore ini} memakai mobil properti, tanpa kejadian sungguhan.',
        'Balai Suryalaya','sore ini')
    add('NON_EVENT','forecast','{OFFICER-ARG:Petugas} mengingatkan potensi {FALSE-EVENT:banjir} di {PLACE-ARG:Desa Wanamerta} {TIME-ARG:besok pagi}; belum ada laporan kejadian.',
        'Desa Wanamerta','besok pagi',['Petugas'])
    add('NON_EVENT','denial','{OFFICER-ARG:Kepala desa} menyatakan tidak terjadi {FALSE-EVENT:gempa} di {PLACE-ARG:Desa Renggawana} {TIME-ARG:tadi malam}.',
        'Desa Renggawana','tadi malam',['Kepala desa'])
    add('NON_EVENT','metaphor','{OFFICER-ARG:Pemilik toko} menyebut {FALSE-EVENT:banjir} pesanan {TIME-ARG:sejak pagi ini}; itu promosi dagangan.',
        time='sejak pagi ini',parties=['Pemilik toko'])
    add('NON_EVENT','prevention','{OFFICER-ARG:Relawan sekolah} membahas pencegahan {FALSE-EVENT:kebakaran} di {PLACE-ARG:Balai Cikartika} {TIME-ARG:siang ini}.',
        'Balai Cikartika','siang ini',['Relawan sekolah'])
    add('NON_EVENT','education','{OFFICER-ARG:Guru} menjelaskan prosedur menghadapi {FALSE-EVENT:gempa} di {PLACE-ARG:Sekolah Melatijaya} {TIME-ARG:pagi tadi}, tanpa kejadian nyata.',
        'Sekolah Melatijaya','pagi tadi',['Guru'])
    add('NON_EVENT','statistics','{OFFICER-ARG:Peneliti} membahas angka {FALSE-EVENT:kecelakaan} {TIME-ARG:tahunan}; tidak ada satu kejadian tertentu yang dilaporkan.',
        time='tahunan',parties=['Peneliti'])
    add('NON_EVENT','donation_aggregate','{OFFICER-ARG:Panitia sosial} mengumpulkan donasi bagi penyintas {FALSE-EVENT:banjir} dan {FALSE-EVENT:gempa} dari beragam tahun, tanpa laporan peristiwa baru.',
        parties=['Panitia sosial'])
    add('NON_EVENT','fiction','{OFFICER-ARG:Para pemain} memeragakan {FALSE-EVENT:kebakaran} di panggung {PLACE-ARG:Teater Nawasena} {TIME-ARG:malam ini}; seluruh adegan fiksi.',
        'Teater Nawasena','malam ini',['Para pemain'])

    # Reject accidental source overlaps without screening any model outcome.
    known=set(json.loads((ROOT/'acceptance/known_inputs.json').read_text())['normalized_text_sha256'])
    for item in json.loads((ROOT/'evidence/acceptance_v081/original_run/evidence/reviewed_bundle_frozen.json').read_text())['records']:
        known.add(hashlib.sha256(normal(item['text']).encode()).hexdigest())
    hashes={hashlib.sha256(normal(row['text']).encode()).hexdigest() for row in rows}
    assert len(rows)==50 and len(hashes)==50 and not hashes&known
    counts=Counter(r['gold_label'] for r in rows);assert set(counts.values())=={10}
    support=Counter(label for row in rows for label in row['gold_nara_labels']);assert set(support)==set(ROLES)
    write(out,{'schema':'slr09-final-proposals-0.8.2','created_at':datetime.now(timezone.utc).isoformat(),
        'human_reference_review_completed':False,'model_inference_executed':False,
        'previous_bintang_approval_does_not_approve_these50':True,'records':rows})
    write(ROOT/'data/final_reference_identity_v0.8.2.json',{'records':50,'tokens':sum(support.values()),
        'class_support':counts,'role_support':support,'normalized_exact_overlap_available_sources':0,
        'human_reference_review_completed':False,'model_inference_executed':False,
        'semantic_independence_established':False,'population_representativeness_established':False,
        'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
    print(json.dumps({'records':50,'tokens':sum(support.values()),'status':'PENDING','model_inference_executed':False}))


if __name__=='__main__':build()
