"""Guard korban literal dengan pemeriksaan negasi pada klausa setempat.

Pertahankan subjek dan jumlah dalam span korban yang memiliki bukti luka,
kematian atau kondisi fisik yang diizinkan. Prefix manusia/jumlah hanya
dipulihkan dari teks yang tepat bersebelahan. Tidak menyimpulkan korban
dari ambulans atau evakuasi; token dan span mentah tetap disimpan.
"""
from __future__ import annotations

from copy import deepcopy
import re

import legacy_postprocessing as legacy

VICTIM_GUARD_VERSION = "silar-victim-guard-0.5.0"
ROLE_GUIDELINE_VERSION = "nara-role-guideline-0.2"

CONDITIONS = re.compile(
    r"\b(?:kritis|sesak\s+(?:napas|nafas)|(?:tak|tidak)\s+(?:sadar|sadarkan)\s+diri)\b", re.I)
PERSON = re.compile(
    r"\b(?:korban|orang|warga|petugas|penumpang|pengendara|angkotpengendara|"
    r"sopir|supir|pelajar|siswa|siswi|anak|balita|pekerja|pria|wanita)\b", re.I)
QUANTITY = re.compile(r"\b(?:\d+|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh)\s*$", re.I)
INCIDENT_CONTEXT = re.compile(r"\b(?:kecelakaan|kebakaran|banjir|gempa|tabrak\w*|tewas|korban)\b", re.I)
NEGATED_PREFIX = re.compile(
    r"\b(?:tidak|tak|bukan|tanpa|nihil|belum)\s+(?:(?:ada|terdapat|seorang|satupun|satu|korban|"
    r"orang|warga|yang|mengalami|dalam|keadaan|berada|dinyatakan|dilaporkan|masih|lagi|sedang|pernah|sampai)\s*)*$", re.I)


def _fold(text):
    return " ".join(str(text).casefold().split())


def _allowed_condition(text, span):
    phrase = span.get("text", "")
    folded_phrase, folded_text = _fold(phrase), _fold(text)
    if not folded_phrase:
        return False
    starts = [m.start() for m in re.finditer(re.escape(folded_phrase), folded_text)]
    if not starts:
        return False
    conditions = list(CONDITIONS.finditer(folded_phrase))
    for condition in conditions:
        # Kata "tak/tidak" yang berada DI DALAM cue tidak sadar adalah kondisi,
        # bukan negasi kondisi. Negasi luarnya diperiksa pada prefix sebelum cue.
        local_prefix = folded_phrase[:condition.start()]
        person = bool(PERSON.search(folded_phrase))
        quantified_incident = bool(QUANTITY.search(local_prefix) and INCIDENT_CONTEXT.search(text))
        if not (person or quantified_incident):
            continue
        occurrence_denials = []
        for start in starts:
            prior = folded_text[:start + condition.start()]
            prior = re.split(r"[.;!?]", prior)[-1]
            # Klausa tandingan memulai konteks baru; negasi klausa lain tidak
            # digunakan untuk menolak korban yang dinyatakan positif.
            prior = re.split(r"\b(?:tetapi|namun|sedangkan)\b", prior)[-1]
            prior = " ".join(prior.split()[-9:])
            occurrence_denials.append(bool(NEGATED_PREFIX.search(prior + " ")))
        if not any(occurrence_denials):
            return True
    return False


def apply_reviewed_victim_safety(text, spans):
    """Pertahankan span literal; negasi diperiksa lokal untuk setiap korban.

    Helper historis tidak diubah. Normalisasi globalnya tidak dipakai lagi:
    ia dapat mengambil korban pertama kalimat dan membuang subjek/kuantitas.
    """
    from silar_nara_composition import locate, TOKEN, QUANTITIES, PERSON_NOUNS
    guarded, flags = deepcopy(spans), []
    expanded_people = set(PERSON_NOUNS) | {"pengendara", "pedagang", "penghuni", "pejalan", "bayi", "balita", "pria", "wanita", "sopir", "supir"}
    chain = expanded_people | set(QUANTITIES) | {'ada', 'terdapat', 'laporan', 'yang',
        'mengalami', 'dalam', 'keadaan', 'dinyatakan', 'dilaporkan', 'seorang',
        'pun', 'satupun', 'kaki'}
    chain_pattern = '|'.join(re.escape(word) for word in sorted(chain))
    denial = re.compile(r"\b(?:tanpa|nihil|bukan|belum|tidak|tak)\s+(?:(?:" + chain_pattern + r"|\d+)\s+)*$", re.I)
    for role, kind, patterns in [("DEATHVICTIM-ARG", "DEATH", legacy.DEATH_EVIDENCE_PATTERNS),
                                 ("WOUNDVICTIM-ARG", "WOUND", legacy.WOUND_EVIDENCE_PATTERNS)]:
        kept = []
        for original in spans.get(role, []):
            phrase = original.get("text", "")
            location = locate(phrase, text)
            is_condition = role == "WOUNDVICTIM-ARG" and bool(CONDITIONS.search(phrase))
            evidence = legacy.has_any_pattern(phrase, patterns)
            if is_condition and not evidence:
                evidence = _allowed_condition(text, original)
            if not evidence:
                flags.append(kind + "_VICTIM_SUPPRESSED_NO_" + kind + "_EVIDENCE")
                continue
            # Prefix hingga cue, bukan semua negasi di narasi. "Tidak sadar"
            # adalah cue fisik; kata tidak di dalam cue tidak menjadi prefix.
            cues = list(CONDITIONS.finditer(phrase)) if is_condition else [m for pattern in patterns for m in re.finditer(pattern, phrase, re.I)]
            denied = False
            if location and cues:
                cue = min(cues, key=lambda m:m.start())
                prior = text[:location["start"] + cue.start()]
                prior = re.split(r"[.;!?]|\b(?:tetapi|namun|sedangkan)\b", prior, flags=re.I)[-1]
                denied = bool(denial.search(prior + " "))
            elif not location:
                # Kemunculan berulang yang memiliki negasi tidak boleh
                # dinormalisasi dengan mengambil korban pertama secara global.
                folded = _fold(text)
                for occurrence in re.finditer(re.escape(_fold(phrase)), folded):
                    prior = re.split(r"[.;!?]|\b(?:tetapi|namun|sedangkan)\b", folded[:occurrence.start()], flags=re.I)[-1]
                    denied |= bool(denial.search(prior + " "))
            if denied:
                flags.append(kind + "_VICTIM_SUPPRESSED_BY_NEGATION")
                continue
            item = deepcopy(original)
            if location:
                words = list(TOKEN.finditer(text))
                first, last = location["start_token"], location["end_token"]
                head = words[first].group().casefold()
                # Pulihkan hanya prefix jumlah/manusia yang tepat bersebelahan
                # dengan span korban. Tidak menyimpulkan dari ambulans/evakuasi.
                if first and head in expanded_people and (words[first-1].group().casefold() in QUANTITIES | {"seorang"} or words[first-1].group().isdigit()):
                    first -= 1
                elif first and (head in {"terluka", "luka", "cedera", "meninggal", "tewas", "wafat", "kritis"}):
                    p = first - 1
                    if words[p].group().casefold() == "kaki" and p and words[p-1].group().casefold() == "pejalan":
                        p -= 1
                    if words[p].group().casefold() in expanded_people:
                        first = p
                        if first and (words[first-1].group().casefold() in QUANTITIES | {"seorang"} or words[first-1].group().isdigit()):
                            first -= 1
                item["text"] = text[words[first].start():words[last].end()]
                item["source"] = "LOCAL_GUARD_PRESERVED_LITERAL_VICTIM_SPAN"
            if item["text"] not in {x["text"] for x in kept}:
                kept.append(item)
        guarded[role] = kept
    return guarded, list(dict.fromkeys(flags))
