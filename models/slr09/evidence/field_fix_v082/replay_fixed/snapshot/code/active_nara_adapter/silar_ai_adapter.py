"""Adapter SLR09 untuk keluaran inferensi TanggapMakna/SILAR yang tersedia.

Hanya memakai standard library. Tidak memuat model, menjalankan training,
menulis database, atau melakukan Human Verification. INFORMATION-ARG dipetakan
ke impacts sebagai usulan AI sesuai pilihan A pengguna.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from silar_postprocessing import (
    POSTPROCESSING_VERSION, filter_negated_fallback_times, filter_spatial_information,
    filter_nonimpact_information, filter_explicitly_unaffected_objects,
)
from silar_nara_composition import compose_fields


ADAPTER_VERSION = "silar-adapter-0.5.1"
FUSION_VERSION = "silar-fusion-a4.22-0.1.0"
EVENT_CATEGORIES = ("FLOOD", "EARTHQUAKE", "FIRE", "ACCIDENT", "NON_EVENT")
NARA_LABELS = (
    "O", "ACCIDENT-EVENT", "AFFECTEDOBJECTS-ARG", "DEATHVICTIM-ARG",
    "EARTHQUAKE-EVENT", "FALSE-EVENT", "FIRE-EVENT", "FLOOD-EVENT",
    "INFORMATION-ARG", "OFFICER-ARG", "PLACE-ARG", "REASON-ARG",
    "STREET-ARG", "TIME-ARG", "WOUNDVICTIM-ARG",
)
EXTRACTION_FIELDS = (
    "location_text", "time_text", "occurred_at", "involved_parties",
    "impacts", "victims", "affected_objects",
)
WARNING_CODES = frozenset({
    "INFORMATION_AS_IMPACT_SUGGESTION", "TIME_FROM_DETERMINISTIC_FALLBACK",
})
TOKEN_PATTERN = re.compile(r"\w+(?:[-']\w+)*|[^\w\s]", flags=re.UNICODE)


class AdapterValidationError(ValueError):
    """Keluaran tidak memenuhi kontrak; caller harus menangani kegagalan."""


class CalibrationRequiredError(AdapterValidationError):
    """Aturan confidence memerlukan konfigurasi kalibrasi eksplisit."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdapterValidationError(message)


def _text(value: Any, name: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{name}: string tidak kosong diperlukan")
    return value


def _probability(value: Any, name: str) -> float:
    _require(type(value) in (int, float), f"{name}: angka diperlukan")
    number = float(value)
    _require(math.isfinite(number) and 0 <= number <= 1, f"{name}: harus dalam rentang 0..1")
    return number


def _json_copy(value: Any, name: str = "raw_output", _active: set[int] | None = None) -> Any:
    """Salin JSON tanpa mengubah tipe atau mengizinkan NaN/objek arbitrer."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        _require(math.isfinite(value), f"{name}: NaN/Infinity tidak diperbolehkan")
        return value
    _require(type(value) in (dict, list), f"{name}: nilai harus kompatibel JSON")
    active = set() if _active is None else _active
    _require(id(value) not in active, f"{name}: referensi melingkar tidak diperbolehkan")
    active.add(id(value))
    try:
        if isinstance(value, list):
            return [_json_copy(item, name, active) for item in value]
        _require(all(isinstance(key, str) for key in value), f"{name}: key harus string")
        return {key: _json_copy(item, name, active) for key, item in value.items()}
    finally:
        active.remove(id(value))


def _model_version(model_version: str) -> str:
    version = f"{_text(model_version, 'model_version')}|{ADAPTER_VERSION}"
    _require(len(version) <= 100, "model_version gabungan melebihi varchar(100)")
    return version


def _display_text(text: str) -> str:
    """Normalisasi tampilan yang sama dengan helper notebook Fusion v1.1."""
    text = re.sub(r"\s+([,;:!?])", r"\1", text)
    text = re.sub(r"(?<=\d)\s*\.\s*(?=\d)", ".", text)
    text = re.sub(r"\s+\.", ".", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _grounded(text: str, narrative: str) -> bool:
    # Helper lama menyisipkan spasi di sekitar punctuation ketika merangkai
    # token. Cocokkan batas kata atau urutan token, bukan substring di tengah
    # kata. Pemeriksaan ini tetap tidak membuktikan kebenaran semantik.
    fragment = _display_text(text).casefold()
    source = _display_text(narrative).casefold()
    left = r"(?<!\w)" if fragment[0].isalnum() or fragment[0] == "_" else ""
    right = r"(?!\w)" if fragment[-1].isalnum() or fragment[-1] == "_" else ""
    if re.search(left + re.escape(fragment) + right, source):
        return True
    needle = [match.group(0).casefold() for match in TOKEN_PATTERN.finditer(text)]
    haystack = [match.group(0).casefold() for match in TOKEN_PATTERN.finditer(narrative)]
    return bool(needle) and any(
        haystack[index:index + len(needle)] == needle
        for index in range(len(haystack) - len(needle) + 1)
    )


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        clean = _display_text(value)
        if clean not in result:
            result.append(clean)
    return result


def _joined(values: list[str]) -> str | None:
    clean = _unique(values)
    return "; ".join(clean) if clean else None


def _read_sena(raw: Any) -> tuple[str, float]:
    _require(isinstance(raw, dict), "event_classifier harus object")
    category = raw.get("label")
    _require(category in EVENT_CATEGORIES, "Label SENA tidak dikenali")
    confidence = _probability(raw.get("confidence"), "SENA confidence")
    probabilities = raw.get("probabilities")
    _require(isinstance(probabilities, dict), "SENA probabilities harus object")
    _require(set(probabilities) == set(EVENT_CATEGORIES), "SENA probabilities harus mencakup tepat lima kelas")
    probs = {key: _probability(value, f"probabilities.{key}") for key, value in probabilities.items()}
    _require(math.isclose(sum(probs.values()), 1.0, abs_tol=1e-6), "Jumlah probabilitas SENA tidak mendekati 1")
    _require(math.isclose(probs[category], confidence, abs_tol=1e-6), "Confidence tidak cocok dengan probabilitas kategori")
    _require(confidence + 1e-6 >= max(probs.values()), "Kategori SENA bukan kelas dengan probabilitas tertinggi")
    return category, confidence


def _validate_tokens(tokens: Any, narrative: str) -> tuple[int, int]:
    _require(isinstance(tokens, list) and bool(tokens), "srl_token_predictions harus list tidak kosong")
    source_tokens = list(TOKEN_PATTERN.finditer(narrative))
    _require(len(tokens) <= len(source_tokens), "Jumlah prediksi NARA melebihi token narasi")
    for index, item in enumerate(tokens):
        _require(isinstance(item, dict), f"Token {index} harus object")
        source = source_tokens[index]
        _require(type(item.get("start")) is int and type(item.get("end")) is int, f"Offset token {index} harus integer")
        _require((item["start"], item["end"]) == source.span(), f"Offset token {index} tidak cocok dengan narasi")
        _require(item.get("original") == source.group(0), f"Original token {index} tidak cocok dengan narasi")
        _require(item.get("token") == source.group(0).lower(), f"Token lowercase {index} tidak cocok")
        _require(item.get("label") in NARA_LABELS, f"Label NARA pada token {index} tidak dikenali")
        _probability(item.get("confidence"), f"NARA confidence token {index}")
    return len(tokens), len(source_tokens)


def _read_spans(spans: Any, narrative: str) -> dict[str, list[str]]:
    _require(isinstance(spans, dict), "srl_spans harus object")
    expected = set(NARA_LABELS) - {"O"}
    _require(set(spans) == expected, "srl_spans harus mencakup tepat 14 role non-O")
    values: dict[str, list[str]] = {}
    for role in NARA_LABELS[1:]:
        entries = spans[role]
        _require(isinstance(entries, list), f"Span {role} harus list")
        texts: list[str] = []
        for entry in entries:
            _require(isinstance(entry, dict) and entry.get("role") == role, f"Object span {role} tidak valid")
            text = _text(entry.get("text"), f"Span {role}.text")
            _probability(entry.get("mean_confidence"), f"Span {role}.mean_confidence")
            _require(_grounded(text, narrative), f"Span {role} tidak ditemukan pada narasi")
            texts.append(text)
        values[role] = _unique(texts)
    return values


def _validate_extraction(data: Any) -> None:
    _require(isinstance(data, dict) and set(data) == set(EXTRACTION_FIELDS), "normalized_output harus tepat tujuh field A4.22")
    for field in ("location_text", "time_text"):
        _require(data[field] is None or (isinstance(data[field], str) and bool(data[field].strip())), f"{field}: string tidak kosong atau null diperlukan")
    # Versi ini hanya memproyeksikan teks; belum mempunyai normalizer timestamp.
    _require(data["occurred_at"] is None, "Adapter ini belum mendukung konversi occurred_at")
    for field in ("involved_parties", "impacts", "victims", "affected_objects"):
        _require(isinstance(data[field], list), f"{field} harus array")
        _require(all(isinstance(item, str) and bool(item.strip()) for item in data[field]), f"Item {field} harus string tidak kosong")


def adapt_legacy_ai_output(
    legacy_output: dict[str, Any],
    *,
    narrative_id: str,
    sena_model_version: str,
    nara_model_version: str,
) -> dict[str, Any]:
    """Proyeksikan keluaran analyze_report lama tanpa menjalankan komponennya.

    Input wajib: report_text, event_classifier, srl_token_predictions, srl_spans.
    srl_spans harus berasal dari postprocessing/guard caller yang versinya
    dicatat pada trace runtime. Fungsi ini memvalidasi bentuk dan grounding, bukan mengulang
    guard korban atau mendeteksi seluruh konflik semantik.
    """
    _text(narrative_id, "narrative_id")
    raw = _json_copy(legacy_output, "legacy_output")
    _require(isinstance(raw, dict), "legacy_output harus object")
    narrative = _text(raw.get("report_text"), "report_text")
    category, confidence = _read_sena(raw.get("event_classifier"))
    processed, expected = _validate_tokens(raw.get("srl_token_predictions"), narrative)
    roles = _read_spans(raw.get("srl_spans"), narrative)
    warnings: list[dict[str, str]] = []
    filtered_values: list[dict[str, str]] = []
    times = roles["TIME-ARG"]
    time_source = "NARA" if times else "NOT_FOUND"

    # Hanya menerima hasil fallback yang sudah dinyatakan oleh pipeline lama.
    # Tidak menjalankan regex waktu baru atau menebak timestamp di adapter ini.
    legacy_card = raw.get("incident_card")
    if not times and isinstance(legacy_card, dict):
        fallback = legacy_card.get("time", [])
        _require(isinstance(fallback, list), "incident_card.time harus list")
        if fallback:
            _require(legacy_card.get("time_source") == "DETERMINISTIC_FALLBACK", "Waktu tanpa TIME-ARG harus mempunyai asal fallback yang jelas")
            for text in fallback:
                _text(text, "time fallback")
                _require(_grounded(text, narrative), "Time fallback tidak ditemukan pada narasi")
            times, removed = filter_negated_fallback_times(narrative, _unique(fallback))
            filtered_values.extend(removed)
            if times:
                time_source = "DETERMINISTIC_FALLBACK"
                warnings.append({"code": "TIME_FROM_DETERMINISTIC_FALLBACK", "field": "time_text"})

    impacts, removed = filter_spatial_information(narrative, roles["INFORMATION-ARG"])
    filtered_values.extend(removed)
    impacts, removed = filter_nonimpact_information(narrative, impacts)
    filtered_values.extend(removed)
    affected_objects, removed = filter_explicitly_unaffected_objects(narrative, roles['AFFECTEDOBJECTS-ARG'])
    filtered_values.extend(removed)
    if impacts:
        warnings.append({"code": "INFORMATION_AS_IMPACT_SUGGESTION", "field": "impacts"})
    normalized = {
        "location_text": _joined(roles["PLACE-ARG"] + roles["STREET-ARG"]),
        "time_text": _joined(times),
        "occurred_at": None,
        "involved_parties": roles["OFFICER-ARG"],
        "impacts": impacts,
        "victims": _unique(roles["DEATHVICTIM-ARG"] + roles["WOUNDVICTIM-ARG"]),
        "affected_objects": affected_objects,
    }
    normalized, composition = compose_fields(narrative, raw["srl_token_predictions"], normalized)
    _validate_extraction(normalized)
    return {
        "source_context": {
            "narrative_id": narrative_id,
            "narrative_sha256": hashlib.sha256(narrative.encode("utf-8")).hexdigest(),
        },
        "sena_result": {
            "narrative_id": narrative_id,
            "category": category,
            "confidence": confidence,
            "raw_output": _json_copy(raw["event_classifier"]),
            "model_version": _model_version(sena_model_version),
        },
        "nara_result": {
            "narrative_id": narrative_id,
            "raw_output": {
                "srl_token_predictions": _json_copy(raw["srl_token_predictions"]),
                "srl_spans": _json_copy(raw["srl_spans"]),
            },
            "normalized_output": _json_copy(normalized),
            "normalization_warnings": warnings,
            "model_version": _model_version(nara_model_version),
        },
        "adapter_metadata": {
            "adapter_version": ADAPTER_VERSION,
            "information_arg_policy": "A_IMPACT_SUGGESTION",
            "postprocessing_version": POSTPROCESSING_VERSION,
            "filtered_values": filtered_values,
            "nara_tokens_processed": processed,
            "nara_source_tokens": expected,
            "nara_token_coverage_complete": processed == expected,
            "time_source": time_source,
            "timestamp_normalization_supported": False,
            "extraction_ambiguity_detection_supported": False,
            "span_guard_responsibility": "CALLER_POSTPROCESSING",
            "composition": composition,
        },
    }


def fuse_for_silar(
    adapted: dict[str, Any],
    *,
    confidence_threshold: float | None,
    calibration_reference: str | None,
) -> dict[str, Any]:
    """Susun field kartu; threshold wajib dipasok dari kalibrasi yang sah.

    Referensi kalibrasi adalah metadata penelusuran. Keberadaan string tersebut
    tidak membuktikan bahwa pengukuran kalibrasi telah dilakukan.
    """
    if confidence_threshold is None or not isinstance(calibration_reference, str) or not calibration_reference.strip():
        raise CalibrationRequiredError("Threshold dan referensi kalibrasi wajib ditetapkan sebelum Fusion diaktifkan")
    threshold = _probability(confidence_threshold, "confidence_threshold")
    bundle = _json_copy(adapted, "adapted")
    _require(isinstance(bundle, dict), "adapted harus object")
    source = bundle.get("source_context")
    sena = bundle.get("sena_result")
    nara = bundle.get("nara_result")
    metadata = bundle.get("adapter_metadata")
    _require(all(isinstance(item, dict) for item in (source, sena, nara, metadata)), "Envelope adapter tidak lengkap")
    narrative_id = _text(source.get("narrative_id"), "source narrative_id")
    _require(sena.get("narrative_id") == nara.get("narrative_id") == narrative_id, "Sumber narasi SENA dan NARA berbeda")
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", str(source.get("narrative_sha256", "")))), "Hash narasi tidak valid")
    _require(metadata.get("adapter_version") == ADAPTER_VERSION, "Versi adapter tidak didukung")
    category, confidence = _read_sena(sena.get("raw_output"))
    _require(sena.get("category") == category and sena.get("confidence") == confidence, "Proyeksi SENA berbeda dari raw output")
    data = nara.get("normalized_output")
    _validate_extraction(data)
    warnings = nara.get("normalization_warnings")
    _require(isinstance(warnings, list), "normalization_warnings harus list")
    for warning in warnings:
        _require(isinstance(warning, dict) and set(warning) == {"code", "field"}, "Bentuk normalization warning tidak valid")
        _require(warning["code"] in WARNING_CODES and warning["field"] in EXTRACTION_FIELDS, "Kode warning/kemampuan ambiguity belum didukung adapter ini")
    reasons = ["LOW_CLASSIFICATION_CONFIDENCE"] if confidence < threshold else []
    card_data = {"event_type": None if category == "NON_EVENT" else category, **_json_copy(data)}
    return {
        "incident_card_version_fields": {
            "data": card_data,
            "uncertain": bool(reasons),
            "uncertain_reasons": reasons,
            "fusion_version": FUSION_VERSION,
        },
        "integration_signals": {
            "blocked_by_non_event": category == "NON_EVENT",
        },
        "fusion_metadata": {
            "confidence_threshold": threshold,
            "calibration_reference": calibration_reference,
            "extraction_ambiguity_detection_supported": False,
        },
    }
