"""Fifty synthetic reference proposals, with no model imports or inference.

Every category/field/token is an assistant proposal pending human review.
No semantic independence or population representativeness is claimed.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/acceptance'))
from evaluate_acceptance import token_items, ROLES, validate_fields, write, normal


def build():
    destination = ROOT / 'data/final_reference_proposals_v0.8.3.json'
    if destination.exists():
        raise ValueError('Do not overwrite a frozen proposal')
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
                      involved_parties=list(parties), impacts=list(impacts),
                      victims=list(victims), affected_objects=list(objects))
        validate_fields(fields, text)
        assert set(labels) <= set(ROLES)
        index = 1 + sum(r['gold_label'] == label for r in rows)
        rows.append(dict(
            id=f'FINAL083-{label}-{index:02d}', text=text, family=family,
            gold_label=label, gold_fields=fields, gold_nara_labels=labels,
            origin=dict(kind='ASSISTANT_AUTHORED_SYNTHETIC',
                        reference='v0.8.3 synthetic proposal with fictional scenes. No model prediction inspected. Human review pending.'),
            review=dict(status='PENDING', reviewer='', at='', note='')))

    add('FLOOD', 'plain', '{TIME-ARG:Pagi ini} {FLOOD-EVENT:banjir} {INFORMATION-ARG:menggenangi} {AFFECTEDOBJECTS-ARG:dua ruang kelas} di {PLACE-ARG:Desa Sumberteduh}.',
        'Desa Sumberteduh', 'Pagi ini', impacts=['menggenangi dua ruang kelas'], objects=['dua ruang kelas'])
    add('FLOOD', 'object_first', '{AFFECTEDOBJECTS-ARG:Jembatan bambu} {INFORMATION-ARG:hanyut} akibat {FLOOD-EVENT:banjir} di {PLACE-ARG:Dusun Tegalbening} {TIME-ARG:semalam}.',
        'Dusun Tegalbening', 'semalam', impacts=['Jembatan bambu hanyut'], objects=['Jembatan bambu'])
    add('FLOOD', 'response', '{OFFICER-ARG:Tim BPBD} {INFORMATION-ARG:mengevakuasi penduduk} dari {PLACE-ARG:Kampung Sindangteduh} karena {FLOOD-EVENT:banjir} {TIME-ARG:siang tadi}.',
        'Kampung Sindangteduh', 'siang tadi', ['Tim BPBD'], ['mengevakuasi penduduk'])
    add('FLOOD', 'cause', '{REASON-ARG:Saluran tersumbat} menyebabkan {FLOOD-EVENT:banjir} di {PLACE-ARG:Kelurahan Talunbening}; {AFFECTEDOBJECTS-ARG:tiga kios} {INFORMATION-ARG:terendam} {TIME-ARG:sore ini}.',
        'Kelurahan Talunbening', 'sore ini', impacts=['tiga kios terendam'], objects=['tiga kios'])
    add('FLOOD', 'victim', '{FLOOD-EVENT:Banjir} terjadi di {PLACE-ARG:Desa Randuteduh} {TIME-ARG:tadi malam}; {WOUNDVICTIM-ARG:seorang warga terluka}.',
        'Desa Randuteduh', 'tadi malam', ['seorang warga'], victims=['seorang warga terluka'])
    add('FLOOD', 'local_negation', 'Tidak ada korban jiwa ketika {FLOOD-EVENT:banjir} {INFORMATION-ARG:merendam} {AFFECTEDOBJECTS-ARG:empat rumah} di {PLACE-ARG:Dusun Karangbening} {TIME-ARG:subuh tadi}.',
        'Dusun Karangbening', 'subuh tadi', impacts=['merendam empat rumah'], objects=['empat rumah'])
    add('FLOOD', 'real_during_exercise', 'Peserta latihan harus keluar karena {FLOOD-EVENT:banjir} sungguhan {INFORMATION-ARG:menggenangi} {AFFECTEDOBJECTS-ARG:halaman sekolah} di {PLACE-ARG:Desa Kembangteduh} {TIME-ARG:pagi tadi}.',
        'Desa Kembangteduh', 'pagi tadi', impacts=['menggenangi halaman sekolah'], objects=['halaman sekolah'])
    add('FLOOD', 'death', '{DEATHVICTIM-ARG:Dua penduduk meninggal} akibat {FLOOD-EVENT:banjir} di {PLACE-ARG:Kampung Pucukbening} {TIME-ARG:kemarin malam}.',
        'Kampung Pucukbening', 'kemarin malam', ['Dua penduduk'], victims=['Dua penduduk meninggal'])
    add('FLOOD', 'street', '{FLOOD-EVENT:Banjir} {INFORMATION-ARG:memutus} {AFFECTEDOBJECTS-ARG:akses kendaraan} di {STREET-ARG:Jalan Seruniwetan} {TIME-ARG:sejak siang}.',
        'Jalan Seruniwetan', 'sejak siang', impacts=['memutus akses kendaraan'], objects=['akses kendaraan'])
    add('FLOOD', 'rumor_verified', 'Kabar itu sudah diperiksa {OFFICER-ARG:petugas desa}: {FLOOD-EVENT:banjir} memang {INFORMATION-ARG:merendam} {AFFECTEDOBJECTS-ARG:satu gudang} di {PLACE-ARG:Desa Rimbabening} {TIME-ARG:sore tadi}.',
        'Desa Rimbabening', 'sore tadi', ['petugas desa'], ['merendam satu gudang'], objects=['satu gudang'])

    add('EARTHQUAKE', 'plain', '{EARTHQUAKE-EVENT:Gempa} {INFORMATION-ARG:mengguncang} {PLACE-ARG:Desa Arumbunar} {TIME-ARG:tadi siang}.',
        'Desa Arumbunar', 'tadi siang', impacts=['mengguncang Desa Arumbunar'])
    add('EARTHQUAKE', 'object_first', '{AFFECTEDOBJECTS-ARG:Dua tembok rumah} {INFORMATION-ARG:retak} setelah {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Kampung Wanasela} {TIME-ARG:pagi ini}.',
        'Kampung Wanasela', 'pagi ini', impacts=['Dua tembok rumah retak'], objects=['Dua tembok rumah'])
    add('EARTHQUAKE', 'response', 'Setelah {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Kelurahan Tirtabunar} {TIME-ARG:sore tadi}, {OFFICER-ARG:relawan} {INFORMATION-ARG:mendirikan tenda}.',
        'Kelurahan Tirtabunar', 'sore tadi', ['relawan'], ['mendirikan tenda'])
    add('EARTHQUAKE', 'victim', '{EARTHQUAKE-EVENT:Gempa} {INFORMATION-ARG:menyebabkan} {WOUNDVICTIM-ARG:dua penjaga terluka} di {PLACE-ARG:Dusun Sumbarsela} {TIME-ARG:semalam}.',
        'Dusun Sumbarsela', 'semalam', ['dua penjaga'], ['menyebabkan dua penjaga terluka'], ['dua penjaga terluka'])
    add('EARTHQUAKE', 'cause', 'Akibat {REASON-ARG:pergeseran lempeng}, {EARTHQUAKE-EVENT:gempa} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:balai pertemuan} di {PLACE-ARG:Desa Lembahbunar} {TIME-ARG:siang ini}.',
        'Desa Lembahbunar', 'siang ini', impacts=['merusak balai pertemuan'], objects=['balai pertemuan'])
    add('EARTHQUAKE', 'local_negation', '{EARTHQUAKE-EVENT:Gempa} {INFORMATION-ARG:merobohkan} {AFFECTEDOBJECTS-ARG:pagar puskesmas} di {PLACE-ARG:Kampung Tanjungsela} {TIME-ARG:kemarin sore}; semua pasien selamat.',
        'Kampung Tanjungsela', 'kemarin sore', impacts=['merobohkan pagar puskesmas'], objects=['pagar puskesmas'])
    add('EARTHQUAKE', 'real_during_exercise', 'Bukan bagian latihan, {EARTHQUAKE-EVENT:gempa} benar-benar {INFORMATION-ARG:mengguncang} {PLACE-ARG:Desa Baturimba} {TIME-ARG:malam ini}.',
        'Desa Baturimba', 'malam ini', impacts=['mengguncang Desa Baturimba'])
    add('EARTHQUAKE', 'death', '{DEATHVICTIM-ARG:Seorang pedagang meninggal} setelah {EARTHQUAKE-EVENT:gempa} di {PLACE-ARG:Pasar Candrasela} {TIME-ARG:tadi pagi}.',
        'Pasar Candrasela', 'tadi pagi', ['Seorang pedagang'], victims=['Seorang pedagang meninggal'])
    add('EARTHQUAKE', 'street', '{EARTHQUAKE-EVENT:Gempa} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:satu jembatan} di {STREET-ARG:Jalan Puspabunar} {TIME-ARG:subuh tadi}.',
        'Jalan Puspabunar', 'subuh tadi', impacts=['merusak satu jembatan'], objects=['satu jembatan'])
    add('EARTHQUAKE', 'rumor_verified', '{OFFICER-ARG:Petugas BPBD} memastikan {EARTHQUAKE-EVENT:gempa} nyata terjadi di {PLACE-ARG:Dusun Waringinsela} {TIME-ARG:sore ini}, meskipun tidak ada korban.',
        'Dusun Waringinsela', 'sore ini', ['Petugas BPBD'])

    add('FIRE', 'plain', '{FIRE-EVENT:Kebakaran} {INFORMATION-ARG:melalap} {AFFECTEDOBJECTS-ARG:dua bengkel} di {PLACE-ARG:Kelurahan Kenaribening} {TIME-ARG:pagi ini}.',
        'Kelurahan Kenaribening', 'pagi ini', impacts=['melalap dua bengkel'], objects=['dua bengkel'])
    add('FIRE', 'object_first', '{AFFECTEDOBJECTS-ARG:Gudang kain} {INFORMATION-ARG:hangus} akibat {FIRE-EVENT:kebakaran} di {PLACE-ARG:Desa Kertabunar} {TIME-ARG:malam tadi}.',
        'Desa Kertabunar', 'malam tadi', impacts=['Gudang kain hangus'], objects=['Gudang kain'])
    add('FIRE', 'response', '{OFFICER-ARG:Tim pemadam} {INFORMATION-ARG:memadamkan} {FIRE-EVENT:api} di {PLACE-ARG:Pasar Rantingsela} {TIME-ARG:siang tadi}.',
        'Pasar Rantingsela', 'siang tadi', ['Tim pemadam'], ['memadamkan api'])
    add('FIRE', 'victim', '{WOUNDVICTIM-ARG:Seorang pekerja terluka} dalam {FIRE-EVENT:kebakaran} di {PLACE-ARG:Kampung Cemarabunar} {TIME-ARG:subuh tadi}.',
        'Kampung Cemarabunar', 'subuh tadi', ['Seorang pekerja'], victims=['Seorang pekerja terluka'])
    add('FIRE', 'cause', '{FIRE-EVENT:Kebakaran} dipicu {REASON-ARG:kabel terkelupas} di {PLACE-ARG:Desa Pelangisela} {TIME-ARG:sore ini}; {AFFECTEDOBJECTS-ARG:ruang penyimpanan} {INFORMATION-ARG:rusak}.',
        'Desa Pelangisela', 'sore ini', impacts=['ruang penyimpanan rusak'], objects=['ruang penyimpanan'])
    add('FIRE', 'local_negation', '{FIRE-EVENT:Kebakaran} {INFORMATION-ARG:menghanguskan} {AFFECTEDOBJECTS-ARG:satu kedai} di {PLACE-ARG:Dusun Kemuningteduh} {TIME-ARG:kemarin malam}, tanpa korban luka.',
        'Dusun Kemuningteduh', 'kemarin malam', impacts=['menghanguskan satu kedai'], objects=['satu kedai'])
    add('FIRE', 'real_during_exercise', 'Latihan dihentikan saat {FIRE-EVENT:kebakaran} sungguhan {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:mobil logistik} di {PLACE-ARG:Lapangan Puspatirta} {TIME-ARG:pagi tadi}.',
        'Lapangan Puspatirta', 'pagi tadi', impacts=['merusak mobil logistik'], objects=['mobil logistik'])
    add('FIRE', 'death', '{FIRE-EVENT:Kebakaran} di {PLACE-ARG:Desa Gunungbening} {TIME-ARG:dini hari} {INFORMATION-ARG:menyebabkan} {DEATHVICTIM-ARG:dua penghuni meninggal}.',
        'Desa Gunungbening', 'dini hari', ['dua penghuni'], ['menyebabkan dua penghuni meninggal'], ['dua penghuni meninggal'])
    add('FIRE', 'street', '{FIRE-EVENT:Api} {INFORMATION-ARG:membakar} {AFFECTEDOBJECTS-ARG:atap toko} di {STREET-ARG:Jalan Wijayabunar} {TIME-ARG:sejak siang}.',
        'Jalan Wijayabunar', 'sejak siang', impacts=['membakar atap toko'], objects=['atap toko'])
    add('FIRE', 'rumor_verified', 'Video itu bukan rekayasa. {FIRE-EVENT:Kebakaran} memang {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:dua warung} di {PLACE-ARG:Kampung Ranubenara} {TIME-ARG:tadi malam}.',
        'Kampung Ranubenara', 'tadi malam', impacts=['merusak dua warung'], objects=['dua warung'])

    add('ACCIDENT', 'plain', '{ACCIDENT-EVENT:Kecelakaan} {INFORMATION-ARG:melibatkan} {AFFECTEDOBJECTS-ARG:dua angkot} di {STREET-ARG:Jalan Padmateduh} {TIME-ARG:siang ini}.',
        'Jalan Padmateduh', 'siang ini', impacts=['melibatkan dua angkot'], objects=['dua angkot'])
    add('ACCIDENT', 'object_first', '{AFFECTEDOBJECTS-ARG:Satu minibus} {INFORMATION-ARG:terguling} dalam {ACCIDENT-EVENT:kecelakaan} di {PLACE-ARG:Desa Waringinbunar} {TIME-ARG:pagi tadi}.',
        'Desa Waringinbunar', 'pagi tadi', impacts=['Satu minibus terguling'], objects=['Satu minibus'])
    add('ACCIDENT', 'response', '{OFFICER-ARG:Petugas kepolisian} {INFORMATION-ARG:mengatur lalu lintas} setelah {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Kenarisela} {TIME-ARG:sore ini}.',
        'Jalan Kenarisela', 'sore ini', ['Petugas kepolisian'], ['mengatur lalu lintas'])
    add('ACCIDENT', 'victim', '{ACCIDENT-EVENT:Kecelakaan} di {PLACE-ARG:Kelurahan Rantingbunar} {TIME-ARG:semalam} {INFORMATION-ARG:mengakibatkan} {WOUNDVICTIM-ARG:seorang penumpang terluka}.',
        'Kelurahan Rantingbunar', 'semalam', ['seorang penumpang'], ['mengakibatkan seorang penumpang terluka'], ['seorang penumpang terluka'])
    add('ACCIDENT', 'cause', 'Karena {REASON-ARG:ban pecah}, {ACCIDENT-EVENT:kecelakaan} {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:satu truk} di {STREET-ARG:Jalan Talunsela} {TIME-ARG:subuh tadi}.',
        'Jalan Talunsela', 'subuh tadi', impacts=['merusak satu truk'], objects=['satu truk'])
    add('ACCIDENT', 'local_negation', 'Semua orang selamat dalam {ACCIDENT-EVENT:kecelakaan} di {PLACE-ARG:Desa Pucukbunar} {TIME-ARG:malam ini}, tetapi {AFFECTEDOBJECTS-ARG:dua motor} {INFORMATION-ARG:rusak}.',
        'Desa Pucukbunar', 'malam ini', impacts=['dua motor rusak'], objects=['dua motor'])
    add('ACCIDENT', 'real_during_exercise', 'Ketika peserta berlatih, {ACCIDENT-EVENT:kecelakaan} nyata {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:mobil pengantar} di {PLACE-ARG:Halaman Gedung Arumteduh} {TIME-ARG:sore tadi}.',
        'Halaman Gedung Arumteduh', 'sore tadi', impacts=['merusak mobil pengantar'], objects=['mobil pengantar'])
    add('ACCIDENT', 'death', '{DEATHVICTIM-ARG:Seorang sopir meninggal} akibat {ACCIDENT-EVENT:kecelakaan} di {STREET-ARG:Jalan Candrabunar} {TIME-ARG:kemarin pagi}.',
        'Jalan Candrabunar', 'kemarin pagi', ['Seorang sopir'], victims=['Seorang sopir meninggal'])
    add('ACCIDENT', 'cause', '{ACCIDENT-EVENT:Kecelakaan} terjadi akibat {REASON-ARG:jarak pandang terbatas} di {PLACE-ARG:Desa Langitsela} {TIME-ARG:tadi malam}.',
        'Desa Langitsela', 'tadi malam')
    add('ACCIDENT', 'rumor_verified', '{OFFICER-ARG:Polisi} membenarkan laporan {ACCIDENT-EVENT:kecelakaan} yang {INFORMATION-ARG:merusak} {AFFECTEDOBJECTS-ARG:bus sekolah} di {PLACE-ARG:Kampung Pandanbunar} {TIME-ARG:siang tadi}.',
        'Kampung Pandanbunar', 'siang tadi', ['Polisi'], ['merusak bus sekolah'], objects=['bus sekolah'])

    add('NON_EVENT', 'simulation', '{OFFICER-ARG:Panitia pelatihan} memeragakan {FALSE-EVENT:kebakaran} di {PLACE-ARG:Balai Pucukteduh} {TIME-ARG:pagi ini}; api dan kerusakannya hanya properti.',
        'Balai Pucukteduh', 'pagi ini', ['Panitia pelatihan'])
    add('NON_EVENT', 'exercise_only', 'Yang tampak sebagai {FALSE-EVENT:kecelakaan} di {PLACE-ARG:Lapangan Talunbunar} {TIME-ARG:siang tadi} adalah adegan latihan. Tidak ada {FALSE-EVENT:kecelakaan} sungguhan.',
        'Lapangan Talunbunar', 'siang tadi')
    add('NON_EVENT', 'forecast', '{OFFICER-ARG:Petugas desa} mengumumkan risiko {FALSE-EVENT:banjir} di {PLACE-ARG:Desa Wanasumur} {TIME-ARG:pekan depan}; belum ada kejadian yang dilaporkan.',
        'Desa Wanasumur', 'pekan depan', ['Petugas desa'])
    add('NON_EVENT', 'denial', 'Setelah pemeriksaan, {OFFICER-ARG:relawan} menyatakan kabar {FALSE-EVENT:gempa} di {PLACE-ARG:Dusun Kertateduh} {TIME-ARG:semalam} tidak benar.',
        'Dusun Kertateduh', 'semalam', ['relawan'])
    add('NON_EVENT', 'metaphor', '{OFFICER-ARG:Pedagang} berkata {FALSE-EVENT:banjir} pembeli {TIME-ARG:sore ini}; yang dimaksud adalah banyak pelanggan, bukan peristiwa bencana.',
        time='sore ini', parties=['Pedagang'])
    add('NON_EVENT', 'prevention', '{OFFICER-ARG:Warga} menghadiri penyuluhan pencegahan {FALSE-EVENT:kebakaran} di {PLACE-ARG:Balai Cemarabening} {TIME-ARG:siang ini}. Kegiatan itu tidak melaporkan {FALSE-EVENT:kebakaran} tertentu.',
        'Balai Cemarabening', 'siang ini', ['Warga'])
    add('NON_EVENT', 'education', '{OFFICER-ARG:Instruktur} mengajarkan prosedur menghadapi {FALSE-EVENT:gempa} di {PLACE-ARG:Sekolah Tunasbunar} {TIME-ARG:pagi tadi}. Semua contoh berasal dari bahan pelajaran.',
        'Sekolah Tunasbunar', 'pagi tadi', ['Instruktur'])
    add('NON_EVENT', 'statistics', '{OFFICER-ARG:Peneliti transportasi} mengulas tren {FALSE-EVENT:kecelakaan} {TIME-ARG:lima tahun terakhir}, tanpa menyebut satu kejadian yang sedang dilaporkan.',
        time='lima tahun terakhir', parties=['Peneliti transportasi'])
    add('NON_EVENT', 'donation_aggregate', '{OFFICER-ARG:Komunitas sosial} mengadakan penggalangan dana untuk penyintas {FALSE-EVENT:banjir} dari beberapa peristiwa lama. Ini pengumuman donasi, bukan laporan kejadian baru.',
        parties=['Komunitas sosial'])
    add('NON_EVENT', 'fiction', '{OFFICER-ARG:Kelompok teater} memainkan adegan {FALSE-EVENT:kecelakaan} di {PLACE-ARG:Gedung Padmabening} {TIME-ARG:malam ini}. Kendaraan rusak hanya properti panggung.',
        'Gedung Padmabening', 'malam ini', ['Kelompok teater'])

    known = set(json.loads((ROOT / 'acceptance/known_inputs.json').read_text())['normalized_text_sha256'])
    for folder in ('data', 'evidence'):
        for path in sorted((ROOT / folder).rglob('*')):
            if not path.is_file() or path.suffix not in {'.json', '.jsonl'}:
                continue
            def collect(value):
                if isinstance(value, dict):
                    if isinstance(value.get('text'), str):
                        known.add(hashlib.sha256(normal(value['text']).encode()).hexdigest())
                    for nested in value.values():
                        collect(nested)
                elif isinstance(value, list):
                    for nested in value:
                        collect(nested)
            if path.suffix == '.json':
                collect(json.loads(path.read_text()))
            else:
                for line in path.read_text().splitlines():
                    if line.strip():
                        collect(json.loads(line))
    hashes = {hashlib.sha256(normal(row['text']).encode()).hexdigest() for row in rows}
    counts = Counter(row['gold_label'] for row in rows)
    support = Counter(label for row in rows for label in row['gold_nara_labels'])
    assert len(rows) == len(hashes) == 50 and not hashes & known
    assert set(counts.values()) == {10} and set(support) == set(ROLES)
    write(destination, dict(schema='slr09-final-proposals-0.8.3',
          created_at=datetime.now(timezone.utc).isoformat(),
          human_reference_review_completed=False, model_inference_executed=False,
          records=rows))
    identity = dict(records=50, tokens=sum(support.values()), class_support=counts,
                    role_support=support, normalized_exact_overlap_available_sources=0,
                    source_known_text_hashes=len(known), human_reference_review_completed=False,
                    model_inference_executed=False, semantic_independence_established=False,
                    population_representativeness_established=False,
                    sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
    write(ROOT / 'data/final_reference_identity_v0.8.3.json', identity)
    print(json.dumps(identity, indent=2))


if __name__ == '__main__':
    build()
