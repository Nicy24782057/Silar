"""Komposisi terbatas dari role NARA dan teks sumber, tanpa inferensi baru.

Tidak menebak role O, kategori SENA, korban, atau timestamp. Hanya span yang
lolos proyeksi/guard baseline dan punya satu lokasi literal yang digunakan.
"""
from __future__ import annotations
from copy import deepcopy
import re

COMPOSITION_VERSION = "silar-nara-composition-0.1.0"
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
                          "anak", "siswa", "pelajar", "mahasiswa", "karyawan"})


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
    """Komposisi hanya memakai field baseline sebagai bukti role yang lolos guard.

    Nilai input tidak diubah. Tidak mengisi lokasi dari token O maupun korban
    dari kata ambulans. Prefix negasi/waktu yang sudah dihapus tidak dipulihkan.
    """
    result = deepcopy(normalized)
    traces = []
    processed = len(token_predictions)
    source_tokens = list(TOKEN.finditer(narrative))
    blocks = []
    for field, role in COMPONENT_FIELDS.items():
        for value in normalized[field]:
            span = locate(value, narrative, processed)
            if span:
                blocks.append({**span, "field": field, "role": role})
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

    # Kata sejak/sekitar mengubah makna temporal; pertahankan jika tepat
    # bersebelahan dengan span waktu dan lokasi frasanya tidak ambigu.
    if normalized["time_text"]:
        times = []
        for value in normalized["time_text"].split("; "):
            span = locate(value, narrative, processed)
            if span and span["start_token"] > 0:
                previous = source_tokens[span["start_token"]-1]
                if previous.group(0).casefold() in {"sejak", "sekitar"}:
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
        length = 1 if words and words[0] == "seorang" else 0
        if len(words) >= 2 and (words[0].isdigit() or words[0] in QUANTITIES) and words[1] in PERSON_NOUNS:
            length = 2
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
