"""Author fresh synthetic proposals after training, without querying either model."""
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
    target = ROOT / 'data/final_reference_proposals_v0.8.4.json'
    if target.exists():
        raise ValueError('Do not overwrite frozen proposals')
    selected = json.loads((ROOT / 'evidence/quality_fix_v084/training29/run_state.json').read_text())
    assert selected['status'] == 'SUCCEEDED'
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
        assert set(labels) <= set(ROLES)
        index = 1 + sum(r['gold_label'] == label for r in rows)
        rows.append(dict(id=f'FINAL084-{label}-{index:02d}', text=text, family=family,
            gold_label=label, gold_fields=fields, gold_nara_labels=labels,
            origin={'kind': 'ASSISTANT_AUTHORED_SYNTHETIC',
                    'reference': 'Fresh v0.8.4 synthetic proposal authored after candidate training; no model predictions used. Not a field report.'},
            review={'status': 'PENDING', 'reviewer': '', 'at': '', 'note': ''}))

    add('FLOOD','plain','{TIME-ARG:Subuh tadi}, {FLOOD-EVENT:banjir} {INFORMATION-ARG:menggenangi} {AFFECTEDOBJECTS-ARG:taman kota} di {PLACE-ARG:Kelurahan Renggapada}.','Kelurahan Renggapada','Subuh tadi',impacts=['menggenangi taman kota'],objects=['taman kota'])
    add('FLOOD','object_first','Di {PLACE-ARG:Desa Banyuarta}, {AFFECTEDOBJECTS-ARG:dua ruang kelas} {INFORMATION-ARG:terendam} {FLOOD-EVENT:banjir} {TIME-ARG:kemarin sore}.','Desa Banyuarta','kemarin sore',impacts=['dua ruang kelas terendam'],objects=['dua ruang kelas'])
    add('FLOOD','response','{OFFICER-ARG:Relawan desa} {INFORMATION-ARG:mengevakuasi warga} ketika {FLOOD-EVENT:banjir} melanda {PLACE-ARG:Kampung Tirtawening} {TIME-ARG:malam tadi}.','Kampung Tirtawening','malam tadi',['Relawan desa'],['mengevakuasi warga'])
    add('FLOOD','real_during_exercise','Sesi latihan dihentikan: {FLOOD-EVENT:banjir} betulan {INFORMATION-ARG:merendam} {AFFECTEDOBJECTS-ARG:ruang arsip} di {PLACE-ARG:Balai Cendranusa} {TIME-ARG:siang ini}.','Balai Cendranusa','siang ini',impacts=['merendam ruang arsip'],objects=['ruang arsip'])
    add('FLOOD','rumor_verified','{OFFICER-ARG:Petugas BPBD} memverifikasi bahwa {FLOOD-EVENT:banjir} di {PLACE-ARG:Dusun Larasbumi} {TIME-ARG:pagi ini} benar terjadi, bukan cerita simulasi.','Dusun Larasbumi','pagi ini',['Petugas BPBD'])
    add('FLOOD','cause','{FLOOD-EVENT:Banjir} akibat {REASON-ARG:tanggul jebol} {INFORMATION-ARG:menutup} {AFFECTEDOBJECTS-ARG:jalan menuju terminal} di {PLACE-ARG:Desa Purnatirta} {TIME-ARG:sejak malam tadi}.','Desa Purnatirta','sejak malam tadi',impacts=['menutup jalan menuju terminal'],objects=['jalan menuju terminal'])
    add('FLOOD','victim','{WOUNDVICTIM-ARG:Seorang warga terluka} saat {FLOOD-EVENT:banjir} di {PLACE-ARG:Kelurahan Nirmalaya} {TIME-ARG:sore tadi}.','Kelurahan Nirmalaya','sore tadi',['Seorang warga'],victims=['Seorang warga terluka'])
    add('FLOOD','death','{FLOOD-EVENT:Banjir} di {PLACE-ARG:Dusun Argalaras} {TIME-ARG:kemarin malam} menyebabkan {DEATHVICTIM-ARG:dua warga meninggal}.','Dusun Argalaras','kemarin malam',['dua warga'],victims=['dua warga meninggal'])
    add('FLOOD','local_negation','{AFFECTEDOBJECTS-ARG:Pagar sekolah} {INFORMATION-ARG:roboh} diterjang {FLOOD-EVENT:banjir} di {PLACE-ARG:Desa Sukmaraya} {TIME-ARG:pagi tadi}; tidak ada korban.','Desa Sukmaraya','pagi tadi',impacts=['Pagar sekolah roboh'],objects=['Pagar sekolah'])
    add('FLOOD','missing_context','{FLOOD-EVENT:Banjir} masih {INFORMATION-ARG:menggenangi} {AFFECTEDOBJECTS-ARG:halaman rumah}; lokasi dan waktunya tidak disebutkan.',impacts=['menggenangi halaman rumah'],objects=['halaman rumah'])

    add('EARTHQUAKE','plain','{TIME-ARG:Menjelang fajar}, {EARTHQUAKE-EVENT:gempa} {INFORMATION-ARG:mengguncang} {PLACE-ARG:Kecamatan Puspareja}.','Kecamatan Puspareja','Menjelang fajar',impacts=['mengguncang Kecamatan Puspareja'])
    add('EARTHQUAKE','object_first','{AFFECTEDOBJECTS-ARG:Tembok perpustakaan} {INFORMATION-ARG:retak} setelah {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Desa Rancawening} {TIME-ARG:siang kemarin}.','Desa Rancawening','siang kemarin',impacts=['Tembok perpustakaan retak'],objects=['Tembok perpustakaan'])
    add('EARTHQUAKE','response','Usai {EARTHQUAKE-EVENT:gempa} {TIME-ARG:malam ini}, {OFFICER-ARG:tim penyelamat} {INFORMATION-ARG:memeriksa bangunan} di {PLACE-ARG:Kampung Candrabuana}.','Kampung Candrabuana','malam ini',['tim penyelamat'],['memeriksa bangunan'])
    add('EARTHQUAKE','real_during_exercise','{EARTHQUAKE-EVENT:Gempa} sungguhan {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:langit-langit aula} di {PLACE-ARG:Pusat Pelatihan Wanasari} {TIME-ARG:pagi tadi}, tepat saat latihan berlangsung.','Pusat Pelatihan Wanasari','pagi tadi',impacts=['merusak langit-langit aula'],objects=['langit-langit aula'])
    add('EARTHQUAKE','rumor_verified','{OFFICER-ARG:Petugas kecamatan} mengonfirmasi kejadian {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Desa Gunalaras} {TIME-ARG:tadi sore}; kabar itu benar.','Desa Gunalaras','tadi sore',['Petugas kecamatan'])
    add('EARTHQUAKE','cause','{REASON-ARG:Aktivitas sesar} memicu {EARTHQUAKE-EVENT:gempa} yang {INFORMATION-ARG:merobohkan} {AFFECTEDOBJECTS-ARG:menara lonceng} di {PLACE-ARG:Kelurahan Weningpada} {TIME-ARG:tengah malam tadi}.','Kelurahan Weningpada','tengah malam tadi',impacts=['merobohkan menara lonceng'],objects=['menara lonceng'])
    add('EARTHQUAKE','victim','Akibat {EARTHQUAKE-EVENT:gempa} {TIME-ARG:siang tadi} di {PLACE-ARG:Desa Binarwangi}, {WOUNDVICTIM-ARG:tiga pekerja terluka}.','Desa Binarwangi','siang tadi',['tiga pekerja'],victims=['tiga pekerja terluka'])
    add('EARTHQUAKE','death','{DEATHVICTIM-ARG:Seorang pedagang meninggal} dalam {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Pasar Suralaras} {TIME-ARG:kemarin pagi}.','Pasar Suralaras','kemarin pagi',['Seorang pedagang'],victims=['Seorang pedagang meninggal'])
    add('EARTHQUAKE','local_negation','Tidak ada yang terluka, namun {EARTHQUAKE-EVENT:gempa} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:atap pos ronda} di {PLACE-ARG:Dusun Padmanala} {TIME-ARG:sore ini}.','Dusun Padmanala','sore ini',impacts=['merusak atap pos ronda'],objects=['atap pos ronda'])
    add('EARTHQUAKE','ongoing','{EARTHQUAKE-EVENT:Gempa susulan} {INFORMATION-ARG:terasa} di {PLACE-ARG:Desa Jayanirmala} {TIME-ARG:sejak pagi}; {OFFICER-ARG:warga} berkumpul di luar.','Desa Jayanirmala','sejak pagi',['warga'],['terasa'])

    add('FIRE','plain','{FIRE-EVENT:Kebakaran} {INFORMATION-ARG:melalap} {AFFECTEDOBJECTS-ARG:gudang kain} di {PLACE-ARG:Kampung Tanjunglaras} {TIME-ARG:dini hari ini}.','Kampung Tanjunglaras','dini hari ini',impacts=['melalap gudang kain'],objects=['gudang kain'])
    add('FIRE','object_first','{TIME-ARG:Kemarin malam}, {AFFECTEDOBJECTS-ARG:tiga kios} {INFORMATION-ARG:hangus} akibat {FIRE-EVENT:kebakaran} di {STREET-ARG:Jalan Weningkarya}.','Jalan Weningkarya','Kemarin malam',impacts=['tiga kios hangus'],objects=['tiga kios'])
    add('FIRE','response','{OFFICER-ARG:Petugas damkar} {INFORMATION-ARG:memadamkan api} dalam {FIRE-EVENT:kebakaran} di {PLACE-ARG:Terminal Argatirta} {TIME-ARG:siang tadi}.','Terminal Argatirta','siang tadi',['Petugas damkar'],['memadamkan api'])
    add('FIRE','real_during_exercise','Di tengah latihan, {FIRE-EVENT:kebakaran} nyata {INFORMATION-ARG:menghanguskan} {AFFECTEDOBJECTS-ARG:ruang genset} di {PLACE-ARG:Gedung Sumanala} {TIME-ARG:sore tadi}; latihan pun dihentikan.','Gedung Sumanala','sore tadi',impacts=['menghanguskan ruang genset'],objects=['ruang genset'])
    add('FIRE','rumor_verified','{OFFICER-ARG:Regu pemadam} memastikan {FIRE-EVENT:kebakaran} di {PLACE-ARG:Desa Kertawening} {TIME-ARG:pagi ini} benar terjadi setelah kabarnya sempat dianggap hoaks.','Desa Kertawening','pagi ini',['Regu pemadam'])
    add('FIRE','cause','{REASON-ARG:Hubungan pendek listrik} menyebabkan {FIRE-EVENT:kebakaran} yang {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:panel kontrol} di {PLACE-ARG:Pabrik Nusalestari} {TIME-ARG:malam tadi}.','Pabrik Nusalestari','malam tadi',impacts=['merusak panel kontrol'],objects=['panel kontrol'])
    add('FIRE','victim','{FIRE-EVENT:Kebakaran} di {PLACE-ARG:Desa Rengganusa} {TIME-ARG:subuh tadi} membuat {WOUNDVICTIM-ARG:dua penghuni terluka}.','Desa Rengganusa','subuh tadi',['dua penghuni'],victims=['dua penghuni terluka'])
    add('FIRE','death','Dalam {FIRE-EVENT:kebakaran} di {PLACE-ARG:Kelurahan Ciptalaras} {TIME-ARG:kemarin siang}, {DEATHVICTIM-ARG:seorang penjaga meninggal}.','Kelurahan Ciptalaras','kemarin siang',['seorang penjaga'],victims=['seorang penjaga meninggal'])
    add('FIRE','local_negation','{FIRE-EVENT:Kebakaran} {INFORMATION-ARG:menghanguskan} {AFFECTEDOBJECTS-ARG:rak buku} di {PLACE-ARG:Balai Weningrasa} {TIME-ARG:pagi tadi}; seluruh penghuni selamat.','Balai Weningrasa','pagi tadi',impacts=['menghanguskan rak buku'],objects=['rak buku'])
    add('FIRE','missing_context','{AFFECTEDOBJECTS-ARG:Sebuah bengkel} {INFORMATION-ARG:hangus} dalam {FIRE-EVENT:kebakaran}. Belum ada keterangan lokasi atau waktu.',impacts=['Sebuah bengkel hangus'],objects=['Sebuah bengkel'])

    add('ACCIDENT','plain','{ACCIDENT-EVENT:Kecelakaan} {INFORMATION-ARG:melibatkan} {AFFECTEDOBJECTS-ARG:bus kota} di {STREET-ARG:Jalan Argawening} {TIME-ARG:pagi ini}.','Jalan Argawening','pagi ini',impacts=['melibatkan bus kota'],objects=['bus kota'])
    add('ACCIDENT','object_first','{AFFECTEDOBJECTS-ARG:Truk pasir} {INFORMATION-ARG:terguling} dalam {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Puspakarya} {TIME-ARG:kemarin malam}.','Jalan Puspakarya','kemarin malam',impacts=['Truk pasir terguling'],objects=['Truk pasir'])
    add('ACCIDENT','response','{OFFICER-ARG:Polisi lalu lintas} {INFORMATION-ARG:mengatur arus kendaraan} usai {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Suryanala} {TIME-ARG:siang tadi}.','Jalan Suryanala','siang tadi',['Polisi lalu lintas'],['mengatur arus kendaraan'])
    add('ACCIDENT','real_during_exercise','Latihan evakuasi terhenti oleh {ACCIDENT-EVENT:kecelakaan} sungguhan: {AFFECTEDOBJECTS-ARG:mobil katering} {INFORMATION-ARG:terbalik} di {STREET-ARG:Jalan Nirmakarya} {TIME-ARG:sore ini}.','Jalan Nirmakarya','sore ini',impacts=['mobil katering terbalik'],objects=['mobil katering'])
    add('ACCIDENT','rumor_verified','{OFFICER-ARG:Petugas kepolisian} membenarkan laporan {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Candralaras} {TIME-ARG:tadi malam}; ini bukan adegan film.','Jalan Candralaras','tadi malam',['Petugas kepolisian'])
    add('ACCIDENT','cause','Karena {REASON-ARG:rem blong}, {ACCIDENT-EVENT:kecelakaan} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:pagar jembatan} di {STREET-ARG:Jalan Wanasukma Raya} {TIME-ARG:pagi tadi}.','Jalan Wanasukma Raya','pagi tadi',impacts=['merusak pagar jembatan'],objects=['pagar jembatan'])
    add('ACCIDENT','victim','{WOUNDVICTIM-ARG:Dua penumpang terluka} dalam {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Banyuprakasa} {TIME-ARG:subuh tadi}.','Jalan Banyuprakasa','subuh tadi',['Dua penumpang'],victims=['Dua penumpang terluka'])
    add('ACCIDENT','death','{ACCIDENT-EVENT:Kecelakaan} di {STREET-ARG:Jalan Tirtaasih} {TIME-ARG:kemarin sore} menyebabkan {DEATHVICTIM-ARG:seorang pengendara meninggal}.','Jalan Tirtaasih','kemarin sore',['seorang pengendara'],victims=['seorang pengendara meninggal'])
    add('ACCIDENT','local_negation','Tak ada korban luka dalam {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Padmalestari} {TIME-ARG:siang ini}, tetapi {AFFECTEDOBJECTS-ARG:sepeda motor} {INFORMATION-ARG:ringsek}.','Jalan Padmalestari','siang ini',impacts=['sepeda motor ringsek'],objects=['sepeda motor'])
    add('ACCIDENT','missing_context','{ACCIDENT-EVENT:Kecelakaan} {INFORMATION-ARG:melibatkan} {AFFECTEDOBJECTS-ARG:dua mobil}. Nama jalan dan waktu belum diberikan.',impacts=['melibatkan dua mobil'],objects=['dua mobil'])

    add('NON_EVENT','simulation','{OFFICER-ARG:Petugas SAR} memimpin simulasi {FALSE-EVENT:banjir} di {PLACE-ARG:Lapangan Renggawening} {TIME-ARG:pagi tadi}; tidak ada kejadian nyata.','Lapangan Renggawening','pagi tadi',['Petugas SAR'])
    add('NON_EVENT','exercise_only','Latihan penanganan {FALSE-EVENT:kecelakaan} di {STREET-ARG:Jalan Sumanusa} {TIME-ARG:siang tadi} memakai kendaraan mainan, tanpa peristiwa sungguhan.','Jalan Sumanusa','siang tadi')
    add('NON_EVENT','simulation','Lantai panggung digerakkan untuk peragaan {FALSE-EVENT:gempa} di {PLACE-ARG:Aula Tirtaanala} {TIME-ARG:sore ini}; bukan {FALSE-EVENT:gempa} yang sebenarnya.','Aula Tirtaanala','sore ini')
    add('NON_EVENT','exercise_only','Dalam latihan di {PLACE-ARG:Lapangan Puspasena} {TIME-ARG:kemarin pagi}, {FALSE-EVENT:banjir} hanya digambarkan pada layar; lingkungan sekitar tetap kering.','Lapangan Puspasena','kemarin pagi')
    add('NON_EVENT','false_alarm','{OFFICER-ARG:Operator posko} membatalkan kabar {FALSE-EVENT:kebakaran} di {PLACE-ARG:Gudang Weningjati} {TIME-ARG:malam tadi}; pemeriksaan tidak menemukan kejadian.','Gudang Weningjati','malam tadi',['Operator posko'])
    add('NON_EVENT','rumor_denied','{OFFICER-ARG:Polisi} membantah isu {FALSE-EVENT:kecelakaan} di {STREET-ARG:Jalan Rancalaras} {TIME-ARG:pagi ini}; kabar tersebut palsu.','Jalan Rancalaras','pagi ini',['Polisi'])
    add('NON_EVENT','prevention','{OFFICER-ARG:Warga} mengikuti penyuluhan pencegahan {FALSE-EVENT:kebakaran} di {PLACE-ARG:Balai Sukmapada} {TIME-ARG:sore tadi}. Kegiatan ini tidak melaporkan kejadian.','Balai Sukmapada','sore tadi',['Warga'])
    add('NON_EVENT','fiction','{FALSE-EVENT:Gempa} dan {FALSE-EVENT:banjir} hanya muncul dalam cerita yang dibaca {OFFICER-ARG:guru} di {PLACE-ARG:Sekolah Puspanirmala} {TIME-ARG:siang ini}.','Sekolah Puspanirmala','siang ini',['guru'])
    add('NON_EVENT','routine','{OFFICER-ARG:Petugas kelurahan} membuka loket administrasi di {PLACE-ARG:Kantor Renggareja} {TIME-ARG:pagi ini}.','Kantor Renggareja','pagi ini',['Petugas kelurahan'])
    add('NON_EVENT','historical_discussion','{OFFICER-ARG:Peneliti} membahas arsip {FALSE-EVENT:banjir} dalam rapat di {PLACE-ARG:Gedung Tirtaaksara} {TIME-ARG:malam ini}, tanpa melaporkan peristiwa baru.','Gedung Tirtaaksara','malam ini',['Peneliti'])

    counts = Counter(r['gold_label'] for r in rows)
    support = Counter(label for r in rows for label in r['gold_nara_labels'])
    assert len(rows) == 50 and set(counts.values()) == {10}
    assert all(support[label] for label in ROLES[1:])
    write(target, dict(schema='slr09-fresh-reference-proposals-0.8.4',
        created_at=datetime.now(timezone.utc).isoformat(), records=rows,
        model_inference_executed=False, source='ASSISTANT_SYNTHETIC_PENDING_HUMAN_REVIEW',
        authored_after_training_finished_at=selected['finished_at']))
    write(ROOT / 'data/final_reference_identity_v0.8.4.json', dict(
        records=50, tokens=sum(len(r['gold_nara_labels']) for r in rows),
        counts=dict(counts), role_support=dict(support),
        proposal_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        new_reference_inference_executed=False, quality_acceptance_approved=False))
    print(json.dumps({'records': 50, 'tokens': sum(support.values()), 'status': '50_PENDING'}))


if __name__ == '__main__':
    build()
