"""Helper murni dari SILAR_Fusion_Engine.ipynb yang telah diaudit.

Isi fungsi/konstanta disalin tanpa perubahan. Hanya impor/globals disesuaikan.
Tidak menyertakan Fusion lama, uncertainty lama, atau Completeness Engine.
Lihat legacy_source_trace.json untuk hash asal setiap fungsi.
"""
import re
import numpy as np
from silar_ai_adapter import NARA_LABELS, TOKEN_PATTERN

EXPECTED_SRL = set(NARA_LABELS)


def tokenize_with_offsets(text):
    result = []

    for match in TOKEN_PATTERN.finditer(text):
        result.append({
            "token": match.group(0).lower(),
            "original": match.group(0),
            "start": match.start(),
            "end": match.end(),
        })

    return result


def contiguous_role_spans(pred_tokens, role):
    spans = []
    current = []

    def flush():
        nonlocal current

        if current:
            spans.append({
                "role": role,
                "text": " ".join(
                    x["original"]
                    for x in current
                ),
                "mean_confidence": float(
                    np.mean([
                        x["confidence"]
                        for x in current
                    ])
                ),
            })

        current = []

    for item in pred_tokens:
        if item["label"] == role:
            current.append(item)
        else:
            flush()

    flush()
    return spans


def all_srl_spans(pred_tokens):
    roles = sorted(EXPECTED_SRL - {"O"})

    return {
        role: contiguous_role_spans(
            pred_tokens,
            role,
        )
        for role in roles
    }


TIME_PATTERNS = [
    r"\b(?:pukul|jam)\s+\d{1,2}(?:[.:]\d{2})?(?:\s*(?:pagi|siang|sore|malam))?\b",
    r"\b(?:tadi|sejak)\s+(?:pagi|siang|sore|malam)\b",
    r"\b(?:pagi|siang|sore|malam)\s+ini\b",
    r"\bmalam\s+tadi\b",
    r"\bkemarin\b",
    r"\bbarusan\b",
    r"\btadi\b",
    r"\bhari\s+ini\b",
]


def time_fallback(text):
    matches = []
    occupied = []

    for pattern in TIME_PATTERNS:
        for m in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            start, end = m.span()

            overlaps = any(
                start < e and end > s
                for s, e in occupied
            )

            if overlaps:
                continue

            matches.append({
                "role": "TIME-FALLBACK",
                "text": m.group(0),
                "source": "DETERMINISTIC_REGEX",
            })

            occupied.append((start, end))

    return sorted(
        matches,
        key=lambda x: text.lower().find(
            x["text"].lower()
        ),
    )


DEATH_NEGATION_PATTERNS = [
    r"\btidak\s+ada\s+(?:korban\s+)?(?:meninggal|korban\s+jiwa)\b",
    r"\btidak\s+terdapat\s+(?:korban\s+)?(?:meninggal|korban\s+jiwa)\b",
    r"\bnihil\s+(?:korban\s+)?(?:meninggal|korban\s+jiwa)\b",
    r"\btanpa\s+(?:korban\s+)?(?:meninggal|korban\s+jiwa)\b",
]


DEATH_EVIDENCE_PATTERNS = [
    r"\bmeninggal\b",
    r"\btewas\b",
    r"\bwafat\b",
    r"\bmenewaskan\b",
    r"\bkorban\s+jiwa\b",
]


WOUND_EVIDENCE_PATTERNS = [
    r"\bterluka\b",
    r"\bluka\b",
    r"\bluka\s+bakar\b",
    r"\bcedera\b",
    r"\bmengalami\s+luka\b",
    r"\bmengeluh\s+sakit\b",
]


def has_any_pattern(text, patterns):
    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in patterns
    )


def has_death_negation(text):
    return has_any_pattern(text, DEATH_NEGATION_PATTERNS)


def normalize_victim_phrase(text, kind):
    number_word = (
        r"(?:\d+|satu|dua|tiga|empat|lima|enam|tujuh|"
        r"delapan|sembilan|sepuluh)"
    )
    person_word = r"(?:orang|korban|pengendara|penumpang|warga)"

    if kind == "wound":
        cue = (
            r"(?:terluka|cedera|luka\s+bakar|"
            r"mengalami\s+luka|mengeluh\s+sakit)"
        )
    else:
        cue = r"(?:meninggal|tewas|wafat)"

    pattern = (
        rf"\b(?:{number_word}\s+)?"
        rf"(?:{person_word}\s+)?"
        rf"{cue}\b"
    )

    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(0) if match else None


def apply_victim_safety(text, spans):
    safety_flags = []

    death_spans = spans.get("DEATHVICTIM-ARG", [])
    wound_spans = spans.get("WOUNDVICTIM-ARG", [])

    death_negated = has_death_negation(text)
    death_evidence = has_any_pattern(
        text,
        DEATH_EVIDENCE_PATTERNS,
    )
    wound_evidence = has_any_pattern(
        text,
        WOUND_EVIDENCE_PATTERNS,
    )

    if death_spans and death_negated:
        spans["DEATHVICTIM-ARG"] = []
        safety_flags.append(
            "DEATH_VICTIM_SUPPRESSED_BY_NEGATION"
        )

    elif death_spans and not death_evidence:
        spans["DEATHVICTIM-ARG"] = []
        safety_flags.append(
            "DEATH_VICTIM_SUPPRESSED_NO_DEATH_EVIDENCE"
        )

    elif death_spans and death_evidence:
        phrase = normalize_victim_phrase(text, "death")
        if phrase:
            spans["DEATHVICTIM-ARG"] = [{
                "role": "DEATHVICTIM-ARG",
                "text": phrase,
                "mean_confidence": float(np.mean([
                    x.get("mean_confidence", 0.0)
                    for x in death_spans
                ])),
                "source": "SRL_PLUS_LEXICAL_EVIDENCE",
            }]

    if wound_spans and not wound_evidence:
        spans["WOUNDVICTIM-ARG"] = []
        safety_flags.append(
            "WOUND_VICTIM_SUPPRESSED_NO_WOUND_EVIDENCE"
        )

    elif wound_spans and wound_evidence:
        phrase = normalize_victim_phrase(text, "wound")
        if phrase:
            spans["WOUNDVICTIM-ARG"] = [{
                "role": "WOUNDVICTIM-ARG",
                "text": phrase,
                "mean_confidence": float(np.mean([
                    x.get("mean_confidence", 0.0)
                    for x in wound_spans
                ])),
                "source": "SRL_PLUS_LEXICAL_EVIDENCE",
            }]

    return spans, safety_flags


def normalize_display_text(text):
    text = str(text)

    text = re.sub(
        r"\s+([,;:!?])",
        r"\1",
        text,
    )

    text = re.sub(
        r"(?<=\d)\s*\.\s*(?=\d)",
        ".",
        text,
    )

    text = re.sub(
        r"\s+\.",
        ".",
        text,
    )

    text = re.sub(
        r"\s{2,}",
        " ",
        text,
    )

    return text.strip()


def span_texts(spans, role):
    return [
        normalize_display_text(x["text"])
        for x in spans.get(role, [])
    ]
