"""A6 allowlist serializers, reusable by the SLR10 ReportDetail reader."""
from django.utils import timezone


def identifier(value):
    return str(value) if value is not None else None


def timestamp(value):
    return value.isoformat().replace("+00:00", "Z") if value else None


def report_snapshot(report):
    result = {"id": str(report.id), "revision": report.revision, "input_revision": report.input_revision}
    for field in ("preparation_status", "workflow_status", "validation_status", "publication_status"):
        result[field] = getattr(report, field)
    for field in (
        "active_bundle_id", "active_narrative_id", "current_card_version_id",
        "official_card_version_id", "active_publication_candidate_id", "published_version_id",
    ):
        result[field] = identifier(getattr(report, field))
    result.update(submitted_at=timestamp(report.submitted_at), closed_at=timestamp(report.closed_at))
    return result


def narrative_data(narrative):
    if narrative is None:
        return None
    return {
        "id": str(narrative.id), "created_at": timestamp(narrative.created_at),
        "report_id": str(narrative.report_id), "bundle_id": str(narrative.bundle_id),
        "parent_id": identifier(narrative.parent_id), "producer_run_id": identifier(narrative.producer_run_id),
        "version_number": narrative.version_number, "text": narrative.text,
        "origin": narrative.origin, "created_by": identifier(narrative.created_by_id),
    }


def transcript_data(transcript):
    if transcript is None:
        return None
    return {
        "id": str(transcript.id), "created_at": timestamp(transcript.created_at),
        "report_id": str(transcript.report_id), "evidence_id": str(transcript.evidence_id),
        "analysis_run_id": str(transcript.analysis_run_id), "text": transcript.text,
        "model_version": transcript.model_version, "duration_ms": transcript.duration_ms,
    }


def sena_data(result):
    if result is None:
        return None
    return {
        "id": str(result.id), "created_at": timestamp(result.created_at),
        "analysis_run_id": str(result.analysis_run_id), "narrative_id": str(result.narrative_id),
        "category": result.category, "confidence": float(result.confidence),
        "raw_output": result.raw_output, "model_version": result.model_version,
    }


def nara_data(result):
    if result is None:
        return None
    return {
        "id": str(result.id), "created_at": timestamp(result.created_at),
        "analysis_run_id": str(result.analysis_run_id), "narrative_id": str(result.narrative_id),
        "raw_output": result.raw_output, "normalized_output": result.normalized_output,
        "normalization_warnings": result.normalization_warnings, "model_version": result.model_version,
    }


def run_data(run, *, content=True):
    from core.models import SENAResult, NARAResult
    sena = SENAResult.objects.filter(analysis_run=run).first() if content else None
    nara = NARAResult.objects.filter(analysis_run=run).first() if content else None
    return {
        "id": str(run.id), "created_at": timestamp(run.created_at), "report_id": str(run.report_id),
        "bundle_id": str(run.bundle_id), "input_narrative_id": identifier(run.input_narrative_id),
        "output_narrative_id": identifier(run.output_narrative_id),
        "used_transcript_id": identifier(run.used_transcript_id), "input_revision": run.input_revision,
        "mode": run.mode, "route": run.route, "status": run.status, "stage": run.stage,
        "model_versions": run.model_versions, "started_at": timestamp(run.started_at),
        "finished_at": timestamp(run.finished_at), "error_code": run.error_code, "timings_ms": run.timings_ms,
        "used_transcript": transcript_data(run.used_transcript) if content and run.used_transcript_id else None,
        "output_narrative": narrative_data(run.output_narrative) if content and run.output_narrative_id else None,
        "sena": sena_data(sena), "nara": nara_data(nara),
    }


def card_data(card):
    if card is None:
        return None
    return {
        "id": str(card.id), "created_at": timestamp(card.created_at), "report_id": str(card.report_id),
        "bundle_id": str(card.bundle_id), "narrative_id": str(card.narrative_id),
        "sena_result_id": str(card.sena_result_id), "nara_result_id": str(card.nara_result_id),
        "parent_id": identifier(card.parent_id), "version_number": card.version_number,
        "source_kind": card.source_kind, "data": card.data, "uncertain": card.uncertain,
        "uncertain_reasons": card.uncertain_reasons, "fusion_version": card.fusion_version,
        "created_by": identifier(card.created_by_id),
    }


def request_data(record, *, replay_authorized=True):
    return {
        "key": str(record.key), "scope": record.scope, "state": record.state,
        "report_id": identifier(record.report_id), "result_type": record.result_type,
        "result_id": identifier(record.result_id), "response_status": record.response_status,
        "error_code": record.error_code, "created_at": timestamp(record.created_at),
        "finished_at": timestamp(record.finished_at), "expires_at": timestamp(record.expires_at),
        "replay_available": bool(
            replay_authorized and record.state in {"SUCCEEDED", "FAILED"}
            and record.response_payload is not None and record.expires_at
            and record.expires_at > timezone.now()
        ),
    }
