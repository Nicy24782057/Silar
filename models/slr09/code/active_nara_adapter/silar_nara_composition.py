"""Komposisi terbatas dari role NARA dan teks sumber, tanpa inferensi baru.

Tidak menebak role O, kategori SENA, korban, atau timestamp. Hanya span yang
lolos proyeksi/guard baseline dan punya satu lokasi literal yang digunakan.
"""
from __future__ import annotations
from copy import deepcopy
import re

COMPOSITION_VERSION = "silar-nara-composition-0.3.1"
ROLE_GUIDELINE_VERSION = "nara-role-guideline-0.2"
TOKEN = re.compile(r"\w+(?:[-']\w+)*|[^\w\s]", re.UNICODE)
COMPONENT_FIELDS = {
    "impacts": "INFORMATION-ARG", "affected_objects": "AFFECTEDOBJECTS-ARG",
    "involved_parties": "OFFICER-ARG", "victims": "GUARDED_VICTIM",
}
QUANTITIES = frozenset({"satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan",
                        "sembilan", "sepuluh", "sebelas", "belasan", "puluhan", "ratusan",
                        "ribuan", "beberapa", "sejumlah"})
PERSON_NOUNS = frozenset({"orang", "warga", "korban", "petugas", "penumpang", "pekerja",
                          "anak", "siswa", "pelajar", "mahasiswa", "karyawan", "pengendara",
                          "pedagang", "penghuni", "pejalan", "balita", "bayi", "sopir", "supir", "penjaga"})
DAMAGE_PREDICATES = frozenset({'merusak','merendam','menggenangi','menghanguskan',
    'melalap','menghancurkan','merobohkan','menutup','menabrak'})


def locate(phrase, source, processed_tokens=None):
    """Offset char/token untuk satu kemunculan; ambigu tetap tanpa perluasan."""
    words = [m.group(0).casefold() for m in TOKEN.finditer(phrase)]
    available = list(TOKEN.finditer(source))
    if processed_tokens is not None:
        available = available[:processed_tokens]
    haystack = [m.group(0).casefold() for m in available]
    starts = [i for i in range(len(haystack)-len(words)+1) if words and haystack[i:i+len(words)] == words]
    if len(starts) != 1:
        return None
    first, last = starts[0], starts[0]+len(words)-1
    return {"start_token": first, "end_token": last, "start": available[first].start(),
            "end": available[last].end(), "text": source[available[first].start():available[last].end()]}


def _trace(field, rule, span, components):
    return {"field": field, "rule": rule, "value": span["text"], "start": span["start"],
            "end": span["end"], "components": components, "origin": "DETERMINISTIC_SOURCE_COMPOSITION"}


def compose_fields(narrative, token_predictions, normalized):
    """Komposisi memakai role yang lolos guard dan prefix literal yang terbatas.

    Nilai input tidak diubah. Tidak mengisi lokasi dari token O maupun korban
    dari kata ambulans. Prefix negasi/waktu yang sudah dihapus tidak dipulihkan.
    """
    normalized = deepcopy(normalized)
    traces = []
    processed = len(token_predictions)
    source_tokens = list(TOKEN.finditer(narrative))
    # A literal quantity immediately before an already accepted object span
    # belongs to that object phrase. Keep raw neural roles unchanged and do
    # not repair ambiguous occurrences or objects removed by upstream guards.
    objects, quantity_locations = [], set()
    locations = (normalized['location_text'] or '').split('; ')
    for value in normalized['affected_objects']:
        span = locate(value, narrative, processed)
        if span and span['start_token'] > 0:
            previous = source_tokens[span['start_token']-1]
            word = previous.group().casefold()
            if word.isdigit() or word in QUANTITIES:
                extended = {'text':narrative[previous.start():span['end']],
                            'start':previous.start(),'end':span['end']}
                objects.append(extended['text'])
                traces.append(_trace('affected_objects','LITERAL_QUANTITY_PREFIX',extended,
                    [{'role':'NARA_OBJECT','text':span['text'],'start':span['start'],'end':span['end']}]))
                for location in locations:
                    loc = locate(location,narrative,processed)
                    if loc and loc['start']==previous.start() and loc['end']==previous.end():
                        quantity_locations.add(location)
                        traces.append(_trace('location_text','QUANTITY_OF_ADJACENT_OBJECT_NOT_LOCATION',loc,
                            [{'role':'NARA_OBJECT','text':span['text'],'start':span['start'],'end':span['end']}]))
                continue
        objects.append(value)
    normalized['affected_objects'] = list(dict.fromkeys(objects))
    if quantity_locations:
        kept = [v for v in locations if v not in quantity_locations]
        normalized['location_text'] = '; '.join(kept) or None
    result = deepcopy(normalized)
    blocks = []
    for field, role in COMPONENT_FIELDS.items():
        for value in normalized[field]:
            span = locate(value, narrative, processed)
            if span:
                blocks.append({**span, "field": field, "role": role})
    # Lokasi dapat menjadi objek literal predikat dampak ("mengguncang Desa").
    # Tidak melompati token O/preposisi dan tidak mengubah field lokasinya.
    if normalized['location_text']:
        for value in normalized['location_text'].split('; '):
            span = locate(value, narrative, processed)
            if span:blocks.append({**span, 'field':'location_text', 'role':'LOCATION'})
    # Pakai frasa yang diproyeksikan/diamankan, bukan role korban mentah yang
    # bisa telah dibuang guard. Hanya rentang bersebelahan yang digabung.
    impacts = []
    for value in normalized["impacts"]:
        anchor = next((b for b in blocks if b["field"] == "impacts" and
                       b["text"].casefold() == value.casefold()), None)
        if anchor is None:
            impacts.append(value)
            continue
        group = [anchor]
        left, right = anchor["start_token"], anchor["end_token"]
        while True:
            neighbors = [b for b in blocks if b not in group and
                         (b["end_token"]+1 == left or b["start_token"] == right+1)]
            if not neighbors:
                break
            # Satu label per token; guard bisa membentuk span lebih panjang.
            # Span bertabrakan tidak dipakai untuk menambah komposisi.
            added = False
            for block in neighbors:
                # Pelaku di kiri predikat adalah pihak, bukan perluasan
                # dampak. Subjek objek rusak di kiri tetap dapat digabung.
                if block['end_token']+1 == left and block['field'] in {'involved_parties','location_text'}:
                    continue
                if any(not (block["end_token"] < g["start_token"] or block["start_token"] > g["end_token"]) for g in group):
                    continue
                # Jangan melintasi punctuation/konjungsi O. Token di setiap
                # komponen harus tersambung tanpa token di antaranya.
                group.append(block)
                left, right = min(left, block["start_token"]), max(right, block["end_token"])
                added = True
            if not added:
                break
        phrase = narrative[source_tokens[left].start():source_tokens[right].end()]
        if phrase not in impacts:
            impacts.append(phrase)
        if len(group) > 1:
            span = {"text": phrase, "start": source_tokens[left].start(), "end": source_tokens[right].end()}
            traces.append(_trace("impacts", "ADJACENT_ROLE_SPANS", span,
                                 [{"role": b["role"], "text": b["text"], "start": b["start"], "end": b["end"]} for b in sorted(group, key=lambda b:b["start"])]))
    result["impacts"] = list(dict.fromkeys(impacts))

    # A neural EVENT span can swallow its following damage predicate. Recover
    # only a listed literal predicate immediately before an accepted object.
    # Raw role labels stay intact; no O token is promoted to a damage role.
    for index, prediction in enumerate(token_predictions):
        role = prediction['label']
        if not role.endswith('-EVENT') or role=='FALSE-EVENT':
            continue
        token = source_tokens[index]
        if token.group().casefold() not in DAMAGE_PREDICATES:
            continue
        prefix = re.split(r'[.;!?]',narrative[:token.start()])[-1]
        if re.search(r'\b(?:tidak|tak|bukan|belum|tanpa)\s+(?:(?:akan|pernah|sedang|lagi|benar-benar)\s+)*$',prefix,re.I):
            continue
        synthetic = re.search(r'\b(?:simulasi|latihan|film|teater|rekaan)\b',prefix,re.I)
        actual = re.search(r'\b(?:sungguhan|nyata|betulan|benar-benar)\b',prefix,re.I)
        if synthetic and not actual:
            continue
        for value in normalized['affected_objects']:
            obj = locate(value,narrative,processed)
            if not obj or obj['start_token']!=index+1:
                continue
            span = {'text':narrative[token.start():obj['end']], 'start':token.start(),'end':obj['end']}
            if span['text'] not in result['impacts']:
                result['impacts'].append(span['text'])
                traces.append(_trace('impacts','DAMAGE_PREDICATE_INSIDE_EVENT_WITH_ADJACENT_OBJECT',span,
                    [{'role':role,'text':token.group(),'start':token.start(),'end':token.end()},
                     {'role':'NARA_OBJECT','text':obj['text'],'start':obj['start'],'end':obj['end']}]))

    # Kata sejak/sekitar mengubah makna temporal; pertahankan jika tepat
    # bersebelahan dengan span waktu dan lokasi frasanya tidak ambigu.
    if normalized["time_text"]:
        times = []
        for value in normalized["time_text"].split("; "):
            span = locate(value, narrative, processed)
            if span and span["start_token"] > 0:
                previous = source_tokens[span["start_token"]-1]
                temporal_prefix = previous.group(0).casefold() in {"sejak", "sekitar", "selama", "setiap"}
                temporal_prefix |= value.casefold() == 'ini' and previous.group(0) in {'hari','pagi','siang','sore','malam'}
                if temporal_prefix:
                    extended = {"text": narrative[previous.start():span["end"]], "start": previous.start(), "end": span["end"]}
                    times.append(extended["text"])
                    traces.append(_trace("time_text", "LITERAL_TIME_MODIFIER", extended,
                                         [{"role": "TIME_SOURCE", "text": span["text"], "start": span["start"], "end": span["end"]}]))
                    continue
            times.append(value)
        result["time_text"] = "; ".join(dict.fromkeys(times))

    # Cakupan pihak berasal dari frasa korban yang sudah lolos pengamanan.
    # Ambil hanya prefix jumlah+nomina manusia, tanpa menebak identitas.
    for value in normalized["victims"]:
        span = locate(value, narrative, processed)
        if not span:
            continue
        tokens = list(TOKEN.finditer(span["text"]))
        words = [m.group(0).casefold() for m in tokens]
        length = 2 if len(words) >= 2 and words[0] == "seorang" and words[1] in PERSON_NOUNS else 0
        if len(words) >= 2 and (words[0].isdigit() or words[0] in QUANTITIES) and words[1] in PERSON_NOUNS:
            length = 2
        if length == 2 and len(words) >= 3 and words[1:3] == ['pejalan','kaki']:
            length = 3
        if not length:
            continue
        end = span["start"] + tokens[length-1].end()
        party = narrative[span["start"]:end]
        if party not in result["involved_parties"]:
            result["involved_parties"].append(party)
            traces.append(_trace("involved_parties", "PERSON_PREFIX_FROM_GUARDED_VICTIM",
                                 {"text": party, "start": span["start"], "end": end},
                                 [{"role": "GUARDED_VICTIM", "text": span["text"], "start": span["start"], "end": span["end"]}]))
    return result, {"version": COMPOSITION_VERSION, "guideline_reference": ROLE_GUIDELINE_VERSION,
                    "rules_applied": traces, "new_neural_inference_executed": False,
                    "training_policy_of_input_model_verified": False}
