"""Tambahan guard sesuai keputusan A: kondisi fisik eksplisit tetap literal.

Guard historis tetap dipakai untuk death dan wound lama. Modul ini hanya
menangani span WOUND yang memuat kritis/sesak napas/tidak sadarkan diri dan
belum memuat cue luka lama. Tidak membuat span dari token O atau inferensi
kendaraan/ambulans/hilang/pengungsi. Prediksi mentah tidak diubah.
"""
from __future__ import annotations

from copy import deepcopy
import re

import legacy_postprocessing as legacy

VICTIM_GUARD_VERSION = "silar-victim-guard-0.4.0"
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
    """Perluasan terbatas untuk kondisi yang disetujui, tanpa relabeling."""
    baseline_input = deepcopy(spans)
    special, ordinary = [], []
    for span in baseline_input.get("WOUNDVICTIM-ARG", []):
        if CONDITIONS.search(span.get("text", "")) and not legacy.has_any_pattern(
                span.get("text", ""), legacy.WOUND_EVIDENCE_PATTERNS):
            special.append(span)
        else:
            ordinary.append(span)
    baseline_input["WOUNDVICTIM-ARG"] = ordinary
    guarded, flags = legacy.apply_victim_safety(text, baseline_input)
    kept = guarded.setdefault("WOUNDVICTIM-ARG", [])
    known = {_fold(r.get("text", "")) for r in kept}
    rejected = False
    for span in special:
        if _allowed_condition(text, span):
            key = _fold(span["text"])
            if key not in known:
                kept.append(deepcopy(span))
                known.add(key)
        else:
            rejected = True
    if rejected and not kept and "WOUND_VICTIM_SUPPRESSED_NO_WOUND_EVIDENCE" not in flags:
        flags.append("WOUND_VICTIM_SUPPRESSED_NO_WOUND_EVIDENCE")
    if kept:
        flags = [f for f in flags if f != "WOUND_VICTIM_SUPPRESSED_NO_WOUND_EVIDENCE"]
    return guarded, flags
