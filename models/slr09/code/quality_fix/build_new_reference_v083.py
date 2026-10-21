"""Freeze new synthetic proposals without importing or querying either model."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/acceptance'))
from evaluate_acceptance import ROLES, token_items, validate_fields, write


def build():
    target = ROOT / 'data/final_reference_proposals_v0.8.3.json'
    if target.exists():
        raise ValueError('Do not overwrite frozen proposals')
    rows = []

    def add(label, family, marked, location=None, time=None, parties=(), impacts=(), victims=(), objects=()):
        text, spans, end = '', [], 0
        for match in re.finditer(r'\{([A-Z-]+):([^}]+)\}', marked):
            text += marked[end:match.start()]
            start = len(text)
            text += match[2]
            spans.append((start, len(text), match[1]))
            end = match.end()
        text += marked[end:]
        labels = [next((role for a, b, role in spans if a <= t.start() and t.end() <= b), 'O')
                  for t in token_items(text)]
        fields = dict(location_text=location, time_text=time, occurred_at=None,
            involved_parties=list(parties), impacts=list(impacts), victims=list(victims), affected_objects=list(objects))
        validate_fields(fields, text)
        if not set(labels) <= set(ROLES):
            raise ValueError('Unknown token role')
        index = 1 + sum(r['gold_label'] == label for r in rows)
        rows.append(dict(id=f'FINAL083-{label}-{index:02d}', text=text, family=family,
            gold_label=label, gold_fields=fields, gold_nara_labels=labels,
            origin={'kind': 'ASSISTANT_AUTHORED_SYNTHETIC',
                    'reference': 'New v0.8.3 synthetic proposal. No model prediction used to author this reference; not a field report.'},
            review={'status': 'PENDING', 'reviewer': '', 'at': '', 'note': ''}))

    add('FLOOD','plain','{FLOOD-EVENT:Banjir} {INFORMATION-ARG:memutus} {AFFECTEDOBJECTS-ARG:akses pasar} di {PLACE-ARG:Kelurahan Puspanala} {TIME-ARG:sejak subuh}.','Kelurahan Puspanala','sejak subuh',impacts=['memutus akses pasar'],objects=['akses pasar'])
    add('FLOOD','object_first','{AFFECTEDOBJECTS-ARG:Tiga rumah} {INFORMATION-ARG:terendam} {FLOOD-EVENT:banjir} {TIME-ARG:malam kemarin} di {PLACE-ARG:Dusun Gintungasri}.','Dusun Gintungasri','malam kemarin',impacts=['Tiga rumah terendam'],objects=['Tiga rumah'])
    add('FLOOD','response','{OFFICER-ARG:Regu SAR} {INFORMATION-ARG:mengungsikan penduduk} dari {PLACE-ARG:Desa Sekarwangi} akibat {FLOOD-EVENT:banjir} {TIME-ARG:pagi ini}.','Desa Sekarwangi','pagi ini',['Regu SAR'],['mengungsikan penduduk'])
    add('FLOOD','real_during_exercise','Peserta latihan mengangkat perahu ketika {FLOOD-EVENT:banjir} sungguhan {INFORMATION-ARG:merendam} {AFFECTEDOBJECTS-ARG:gudang beras} di {PLACE-ARG:Dusun Waringinreja} {TIME-ARG:sore tadi}.','Dusun Waringinreja','sore tadi',impacts=['merendam gudang beras'],objects=['gudang beras'])
    add('FLOOD','rumor_verified','{OFFICER-ARG:Petugas kelurahan} mengonfirmasi {FLOOD-EVENT:banjir} di {PLACE-ARG:Kelurahan Mekarnala} {TIME-ARG:malam ini}; informasi tersebut bukan skenario latihan.','Kelurahan Mekarnala','malam ini',['Petugas kelurahan'])
    add('FLOOD','cause','{REASON-ARG:Luapan sungai} menyebabkan {FLOOD-EVENT:banjir} {INFORMATION-ARG:menggenangi} {AFFECTEDOBJECTS-ARG:kebun sayur} di {PLACE-ARG:Desa Karangnusa} {TIME-ARG:siang tadi}.','Desa Karangnusa','siang tadi',impacts=['menggenangi kebun sayur'],objects=['kebun sayur'])
    add('FLOOD','victim','{FLOOD-EVENT:Banjir} di {PLACE-ARG:Desa Palaswangi} {TIME-ARG:kemarin malam} mengakibatkan {WOUNDVICTIM-ARG:seorang warga terluka}.','Desa Palaswangi','kemarin malam',['seorang warga'],victims=['seorang warga terluka'])
    add('FLOOD','death','{DEATHVICTIM-ARG:Dua nelayan meninggal} saat {FLOOD-EVENT:banjir} di {PLACE-ARG:Kampung Rengganala} {TIME-ARG:pagi tadi}.','Kampung Rengganala','pagi tadi',['Dua nelayan'],victims=['Dua nelayan meninggal'])
    add('FLOOD','local_negation','Tak ada korban jiwa, tetapi {FLOOD-EVENT:banjir} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:pagar puskesmas} di {PLACE-ARG:Desa Manggalarum} {TIME-ARG:sore ini}.','Desa Manggalarum','sore ini',impacts=['merusak pagar puskesmas'],objects=['pagar puskesmas'])
    add('FLOOD','ongoing','{TIME-ARG:Sejak tadi malam}, {FLOOD-EVENT:banjir} masih {INFORMATION-ARG:menggenangi} {AFFECTEDOBJECTS-ARG:jalan desa} di {PLACE-ARG:Kampung Cikareja}.','Kampung Cikareja','Sejak tadi malam',impacts=['menggenangi jalan desa'],objects=['jalan desa'])

    add('EARTHQUAKE','plain','{EARTHQUAKE-EVENT:Gempa} {INFORMATION-ARG:mengguncang} {PLACE-ARG:Kecamatan Sukamanah} {TIME-ARG:siang ini}; {OFFICER-ARG:warga} keluar dari rumah.','Kecamatan Sukamanah','siang ini',['warga'],['mengguncang Kecamatan Sukamanah'])
    add('EARTHQUAKE','object_first','{AFFECTEDOBJECTS-ARG:Atap balai warga} {INFORMATION-ARG:ambruk} akibat {EARTHQUAKE-EVENT:gempa} {TIME-ARG:subuh tadi} di {PLACE-ARG:Desa Ciparanti}.','Desa Ciparanti','subuh tadi',impacts=['Atap balai warga ambruk'],objects=['Atap balai warga'])
    add('EARTHQUAKE','response','Setelah {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Dusun Sindangnala} {TIME-ARG:pagi tadi}, {OFFICER-ARG:relawan} {INFORMATION-ARG:mendirikan tenda}.','Dusun Sindangnala','pagi tadi',['relawan'],['mendirikan tenda'])
    add('EARTHQUAKE','real_during_exercise','Instruktur menghentikan latihan karena {EARTHQUAKE-EVENT:gempa} betulan {INFORMATION-ARG:meretakkan} {AFFECTEDOBJECTS-ARG:tembok kelas} di {PLACE-ARG:Sekolah Binarasa} {TIME-ARG:siang tadi}.','Sekolah Binarasa','siang tadi',impacts=['meretakkan tembok kelas'],objects=['tembok kelas'])
    add('EARTHQUAKE','rumor_verified','{OFFICER-ARG:Tim BPBD} memastikan kabar {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Desa Kertanala} {TIME-ARG:tadi malam} benar; {AFFECTEDOBJECTS-ARG:satu rumah} {INFORMATION-ARG:rusak}.','Desa Kertanala','tadi malam',['Tim BPBD'],['satu rumah rusak'],objects=['satu rumah'])
    add('EARTHQUAKE','cause','Akibat {REASON-ARG:pergeseran sesar}, {EARTHQUAKE-EVENT:gempa} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:menara air} di {PLACE-ARG:Kelurahan Tirtanala} {TIME-ARG:sore ini}.','Kelurahan Tirtanala','sore ini',impacts=['merusak menara air'],objects=['menara air'])
    add('EARTHQUAKE','victim','{WOUNDVICTIM-ARG:Dua pedagang terluka} dalam {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Pasar Ciburuan} {TIME-ARG:kemarin pagi}.','Pasar Ciburuan','kemarin pagi',['Dua pedagang'],victims=['Dua pedagang terluka'])
    add('EARTHQUAKE','death','{EARTHQUAKE-EVENT:Gempa} di {PLACE-ARG:Desa Langlangreja} {TIME-ARG:malam tadi} menimbulkan {DEATHVICTIM-ARG:satu korban meninggal}.','Desa Langlangreja','malam tadi',['satu korban'],victims=['satu korban meninggal'])
    add('EARTHQUAKE','local_negation','Tidak ada korban luka setelah {EARTHQUAKE-EVENT:gempa} {TIME-ARG:sore tadi} di {PLACE-ARG:Kampung Pasirnala}; {AFFECTEDOBJECTS-ARG:dinding musala} {INFORMATION-ARG:retak}.','Kampung Pasirnala','sore tadi',impacts=['dinding musala retak'],objects=['dinding musala'])
    add('EARTHQUAKE','ongoing','{EARTHQUAKE-EVENT:Gempa susulan} {INFORMATION-ARG:terasa} di {PLACE-ARG:Desa Wanasukma} {TIME-ARG:malam ini} dan {OFFICER-ARG:warga} menunggu di luar.','Desa Wanasukma','malam ini',['warga'],['terasa'])

    add('FIRE','plain','{FIRE-EVENT:Kebakaran} {INFORMATION-ARG:melalap} {AFFECTEDOBJECTS-ARG:kios buah} di {PLACE-ARG:Pasar Palagan} {TIME-ARG:dini hari tadi}.','Pasar Palagan','dini hari tadi',impacts=['melalap kios buah'],objects=['kios buah'])
    add('FIRE','object_first','{AFFECTEDOBJECTS-ARG:Dua bengkel} {INFORMATION-ARG:hangus} dalam {FIRE-EVENT:kebakaran} di {STREET-ARG:Jalan Nataraya} {TIME-ARG:kemarin sore}.','Jalan Nataraya','kemarin sore',impacts=['Dua bengkel hangus'],objects=['Dua bengkel'])
    add('FIRE','response','{OFFICER-ARG:Regu damkar} {INFORMATION-ARG:memadamkan api} saat {FIRE-EVENT:kebakaran} di {PLACE-ARG:Gudang Puspalaras} {TIME-ARG:siang ini}.','Gudang Puspalaras','siang ini',['Regu damkar'],['memadamkan api'])
    add('FIRE','real_during_exercise','Bukan alat peraga yang terbakar: {FIRE-EVENT:kebakaran} sungguhan {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:kantin} di {PLACE-ARG:Pusat Latihan Wiranala} {TIME-ARG:pagi ini}.','Pusat Latihan Wiranala','pagi ini',impacts=['merusak kantin'],objects=['kantin'])
    add('FIRE','rumor_verified','Pemeriksaan {OFFICER-ARG:petugas desa} membuktikan {FIRE-EVENT:kebakaran} di {PLACE-ARG:Desa Bayumanah} {TIME-ARG:tadi malam} merupakan kejadian nyata.','Desa Bayumanah','tadi malam',['petugas desa'])
    add('FIRE','cause','{REASON-ARG:Tabung gas bocor} memicu {FIRE-EVENT:kebakaran} yang {INFORMATION-ARG:menghanguskan} {AFFECTEDOBJECTS-ARG:dapur warung} di {PLACE-ARG:Kampung Nusaloka} {TIME-ARG:sore tadi}.','Kampung Nusaloka','sore tadi',impacts=['menghanguskan dapur warung'],objects=['dapur warung'])
    add('FIRE','victim','{FIRE-EVENT:Kebakaran} {TIME-ARG:subuh tadi} di {PLACE-ARG:Kelurahan Ringinmanah} mengakibatkan {WOUNDVICTIM-ARG:satu pemilik rumah terluka}.','Kelurahan Ringinmanah','subuh tadi',['satu pemilik rumah'],victims=['satu pemilik rumah terluka'])
    add('FIRE','death','Dalam {FIRE-EVENT:kebakaran} di {PLACE-ARG:Desa Cikamulya} {TIME-ARG:malam kemarin}, {DEATHVICTIM-ARG:seorang pekerja meninggal}.','Desa Cikamulya','malam kemarin',['seorang pekerja'],victims=['seorang pekerja meninggal'])
    add('FIRE','local_negation','{FIRE-EVENT:Kebakaran} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:ruang penyimpanan} di {PLACE-ARG:Balai Naramukti} {TIME-ARG:siang tadi}; semua orang selamat.','Balai Naramukti','siang tadi',impacts=['merusak ruang penyimpanan'],objects=['ruang penyimpanan'])
    add('FIRE','ongoing','{TIME-ARG:Malam ini}, {FIRE-EVENT:api} masih {INFORMATION-ARG:membakar} {AFFECTEDOBJECTS-ARG:tumpukan kayu} di {PLACE-ARG:Dusun Ciparayasih}.','Dusun Ciparayasih','Malam ini',impacts=['membakar tumpukan kayu'],objects=['tumpukan kayu'])

    add('ACCIDENT','plain','{ACCIDENT-EVENT:Kecelakaan} {INFORMATION-ARG:melibatkan} {AFFECTEDOBJECTS-ARG:sepeda motor} di {STREET-ARG:Jalan Sindangarum} {TIME-ARG:pagi tadi}.','Jalan Sindangarum','pagi tadi',impacts=['melibatkan sepeda motor'],objects=['sepeda motor'])
    add('ACCIDENT','object_first','{AFFECTEDOBJECTS-ARG:Mobil pengangkut telur} {INFORMATION-ARG:terbalik} dalam {ACCIDENT-EVENT:kecelakaan} di {PLACE-ARG:Desa Bantarwulan} {TIME-ARG:siang ini}.','Desa Bantarwulan','siang ini',impacts=['Mobil pengangkut telur terbalik'],objects=['Mobil pengangkut telur'])
    add('ACCIDENT','response','{OFFICER-ARG:Petugas polisi} {INFORMATION-ARG:mengatur lalu lintas} setelah {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Madunala} {TIME-ARG:kemarin sore}.','Jalan Madunala','kemarin sore',['Petugas polisi'],['mengatur lalu lintas'])
    add('ACCIDENT','real_during_exercise','Pelatihan dihentikan ketika {ACCIDENT-EVENT:kecelakaan} nyata {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:mobil instruktur} di {PLACE-ARG:Lapangan Sekarnala} {TIME-ARG:sore tadi}.','Lapangan Sekarnala','sore tadi',impacts=['merusak mobil instruktur'],objects=['mobil instruktur'])
    add('ACCIDENT','rumor_verified','Rekaman latihan itu terputus oleh {ACCIDENT-EVENT:kecelakaan} sungguhan di {STREET-ARG:Jalan Giriarum} {TIME-ARG:pagi ini}; {WOUNDVICTIM-ARG:seorang pengendara terluka}.','Jalan Giriarum','pagi ini',['seorang pengendara'],victims=['seorang pengendara terluka'])
    add('ACCIDENT','cause','{REASON-ARG:Ban pecah} memicu {ACCIDENT-EVENT:kecelakaan} di {PLACE-ARG:Desa Wanamanah} {TIME-ARG:malam tadi}; {AFFECTEDOBJECTS-ARG:satu truk} {INFORMATION-ARG:rusak}.','Desa Wanamanah','malam tadi',impacts=['satu truk rusak'],objects=['satu truk'])
    add('ACCIDENT','victim','Akibat {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Sukawening} {TIME-ARG:subuh tadi}, {WOUNDVICTIM-ARG:dua penumpang terluka}.','Jalan Sukawening','subuh tadi',['dua penumpang'],victims=['dua penumpang terluka'])
    add('ACCIDENT','death','{DEATHVICTIM-ARG:Seorang sopir meninggal} pada {ACCIDENT-EVENT:kecelakaan} di {PLACE-ARG:Kampung Palawana} {TIME-ARG:kemarin malam}.','Kampung Palawana','kemarin malam',['Seorang sopir'],victims=['Seorang sopir meninggal'])
    add('ACCIDENT','local_negation','{ACCIDENT-EVENT:Kecelakaan} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:dua motor} di {STREET-ARG:Jalan Puspasukma} {TIME-ARG:siang tadi}, tanpa korban luka.','Jalan Puspasukma','siang tadi',impacts=['merusak dua motor'],objects=['dua motor'])
    add('ACCIDENT','plain','{TIME-ARG:Tadi sore}, {ACCIDENT-EVENT:kecelakaan} {INFORMATION-ARG:melibatkan} {AFFECTEDOBJECTS-ARG:bus sekolah} di {PLACE-ARG:Kelurahan Mekarwening}.','Kelurahan Mekarwening','Tadi sore',impacts=['melibatkan bus sekolah'],objects=['bus sekolah'])

    add('NON_EVENT','exercise_only','Di {PLACE-ARG:Balai Sukmanala} {TIME-ARG:siang ini}, peserta memperagakan {FALSE-EVENT:kecelakaan} dengan kendaraan tiruan; seluruh adegan hanya latihan.','Balai Sukmanala','siang ini')
    add('NON_EVENT','simulation','{OFFICER-ARG:Regu damkar} menggunakan layar untuk simulasi {FALSE-EVENT:kebakaran} di {PLACE-ARG:Aula Giriwening} {TIME-ARG:pagi tadi}; tidak ada kejadian nyata.','Aula Giriwening','pagi tadi',['Regu damkar'])
    add('NON_EVENT','exercise_only','Getaran buatan menandai peragaan {FALSE-EVENT:gempa} di {PLACE-ARG:Pusat Belajar Naramerta} {TIME-ARG:sore ini}, bukan gempa sungguhan.','Pusat Belajar Naramerta','sore ini')
    add('NON_EVENT','simulation','{FALSE-EVENT:Banjir} pada latihan di {PLACE-ARG:Lapangan Kertamanah} {TIME-ARG:kemarin pagi} ditiru dengan kolam kecil; permukiman tetap kering.','Lapangan Kertamanah','kemarin pagi')
    add('NON_EVENT','forecast','{OFFICER-ARG:Petugas} membahas potensi {FALSE-EVENT:banjir} di {PLACE-ARG:Desa Nusalintang} {TIME-ARG:pekan depan}; sampai kini belum ada kejadian.','Desa Nusalintang','pekan depan',['Petugas'])
    add('NON_EVENT','denial','{OFFICER-ARG:Kepala dusun} membantah kabar {FALSE-EVENT:kebakaran} di {PLACE-ARG:Dusun Girimadu} {TIME-ARG:malam tadi}; pemeriksaan tidak menemukan peristiwa tersebut.','Dusun Girimadu','malam tadi',['Kepala dusun'])
    add('NON_EVENT','education','{OFFICER-ARG:Guru} menguraikan teori penyebab {FALSE-EVENT:gempa} di {PLACE-ARG:Sekolah Wanasukma} {TIME-ARG:pagi ini}; ini pelajaran, tanpa peristiwa tertentu.','Sekolah Wanasukma','pagi ini',['Guru'])
    add('NON_EVENT','metaphor','{OFFICER-ARG:Pedagang} berkata tokonya {FALSE-EVENT:banjir} pesanan {TIME-ARG:hari ini}; ungkapan itu berarti banyak pembeli.',time='hari ini',parties=['Pedagang'])
    add('NON_EVENT','fiction','Cerita pendek tentang {FALSE-EVENT:kecelakaan} di negeri rekaan dibacakan {OFFICER-ARG:peserta kelas} {TIME-ARG:sore tadi}; kisahnya fiksi.',time='sore tadi',parties=['peserta kelas'])
    add('NON_EVENT','statistics','{OFFICER-ARG:Peneliti} menyajikan statistik {FALSE-EVENT:kebakaran} tahunan di {PLACE-ARG:Gedung Wanasukma} {TIME-ARG:siang tadi}, tanpa melaporkan kejadian baru.','Gedung Wanasukma','siang tadi',['Peneliti'])

    counts = Counter(r['gold_label'] for r in rows)
    support = Counter(label for r in rows for label in r['gold_nara_labels'])
    assert len(rows) == 50 and set(counts.values()) == {10}
    assert all(support[label] for label in ROLES[1:])
    write(target, dict(schema='slr09-fresh-reference-proposals-0.8.3',
        created_at=datetime.now(timezone.utc).isoformat(), records=rows,
        model_inference_executed=False, source='ASSISTANT_SYNTHETIC_PENDING_HUMAN_REVIEW'))
    write(ROOT / 'data/final_reference_identity_v0.8.3.json', dict(
        records=50, tokens=sum(len(r['gold_nara_labels']) for r in rows),
        counts=dict(counts), role_support=dict(support),
        proposal_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        new_reference_inference_executed=False, quality_acceptance_approved=False))
    print(json.dumps({'records': 50, 'tokens': sum(support.values()), 'status': '50_PENDING'}))


if __name__ == '__main__':
    build()
