"""Data buatan untuk memeriksa adapter; bukan hasil prediksi model AI."""

from __future__ import annotations

import re

from silar_ai_adapter import EVENT_CATEGORIES, NARA_LABELS, TOKEN_PATTERN


def make_synthetic_legacy(
    narrative: str,
    *,
    category: str = "FLOOD",
    confidence: float = 0.9,
    role_phrases: dict[str, list[str]] | None = None,
) -> dict:
    """Bentuk fixture dengan struktur yang sama dengan keluaran notebook lama."""
    role_phrases = role_phrases or {}
    assignments = []
    for role, phrases in role_phrases.items():
        if role not in NARA_LABELS or role == "O":
            raise ValueError("Role fixture tidak valid")
        for phrase in phrases:
            match = re.search(re.escape(phrase), narrative)
            if match is None:
                raise ValueError("Frasa fixture harus literal dari narasi")
            assignments.append((*match.span(), role))
    tokens = []
    for match in TOKEN_PATTERN.finditer(narrative):
        label = next((role for start, end, role in assignments if start <= match.start() and match.end() <= end), "O")
        tokens.append({
            "token": match.group(0).lower(), "original": match.group(0),
            "start": match.start(), "end": match.end(),
            "label": label, "confidence": 0.99,
        })
    # Nilai span fixture dibentuk dari frasa anotasi buatan yang diberikan.
    spans = {role: [] for role in NARA_LABELS if role != "O"}
    for role, phrases in role_phrases.items():
        spans[role] = [{"role": role, "text": phrase, "mean_confidence": 0.99} for phrase in phrases]
    probabilities = {label: (confidence if label == category else (1 - confidence) / 4) for label in EVENT_CATEGORIES}
    return {
        "report_text": narrative,
        "event_classifier": {"label": category, "confidence": confidence, "probabilities": probabilities},
        "srl_token_predictions": tokens,
        "srl_spans": spans,
    }


def demo_fixture() -> dict:
    return make_synthetic_legacy(
        "Banjir di Rajabasa, Jalan Mawar, pukul 14.30. Dua rumah terendam dan satu warga terluka. BPBD berada di lokasi akibat hujan deras.",
        role_phrases={
            "FLOOD-EVENT": ["Banjir"], "PLACE-ARG": ["Rajabasa"],
            "STREET-ARG": ["Jalan Mawar"], "TIME-ARG": ["pukul 14.30"],
            "AFFECTEDOBJECTS-ARG": ["Dua rumah"], "INFORMATION-ARG": ["terendam"],
            "WOUNDVICTIM-ARG": ["satu warga terluka"], "OFFICER-ARG": ["BPBD"],
            "REASON-ARG": ["hujan deras"],
        },
    )
