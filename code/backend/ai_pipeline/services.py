"""A7.4: reserve, execute synchronously, persist stages, finalize after commit."""
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
import logging
import time
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import DatabaseError, connection, transaction
from django.db.models import Max
from django.http import Http404
from django.utils import timezone

from accounts.models import User, Role
from common.api import ApiProblem
from core.audit import record_event
from core.capacity import analysis_slot, create_reserved_run
from core.models import (
    AnalysisRun, EvidenceBundle, IncidentCardVersion, IdempotencyRecord,
    NarrativeVersion, NARAResult, Report, SENAResult, Transcript,
)
from core.mutations import MutationResult, request_digest
from core.permissions import require_owner_draft, require_report_read
from core.validators import card_data as validate_card_data

from .config import options
from .errors import FencedExecution, PipelineFailure, invalid_output
from .execution import process_context
from .output import report_snapshot, run_data
from .pipeline import get_pipeline
from .serializers import canonical_payload
from .sources import EvidenceSource, load_sources, route_for

logger = logging.getLogger(__name__)
ACTIVE = {"RUNNING", "UNKNOWN"}


def json_value(value):
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder, allow_nan=False))


def authorize_analysis(actor, report):
    # Authorization is separate from the NOT_SUBMITTED transition guard:
    # a terminal replay may remain valid after submission, per A7.4.
    require_report_read(actor, report, content=True)
    if actor.role != Role.REPORTER or report.owner_id != actor.id:
        raise Http404


def find_report(actor, report_id):
    report = Report.objects.filter(pk=report_id).first()
    if report is None:
        raise Http404
    authorize_analysis(actor, report)
    return report


def validate_key(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as error:
        raise ApiProblem("INVALID_PAYLOAD", "Idempotency-Key harus UUID.", 400) from error


def replay_for(actor, report, key, payload):
    authorize_analysis(actor, report)
    record = IdempotencyRecord.objects.filter(actor=actor, key=key).first()
    if record is None:
        return None
    if (
        record.scope != f"POST reports/{report.id}/analyses/"
        or record.report_id != report.id or record.request_hash != request_digest(payload)
    ):
        raise ApiProblem("IDEMPOTENCY_MISMATCH", "Key sudah dipakai untuk permintaan berbeda.", 409)
    if record.state in ACTIVE:
        raise ApiProblem("REQUEST_" + record.state, "Baca keadaan analisis tersimpan.", 409)
    if not record.expires_at or record.expires_at <= timezone.now() or record.response_payload is None:
        raise ApiProblem("IDEMPOTENCY_EXPIRED", "Masa replay habis. Baca hasil tersimpan.", 409)
    return MutationResult(
        record.response_payload, record.response_status, record.result_type, record.result_id, True
    )


def check_source(report, run):
    same = (
        report.active_bundle_id == run.bundle_id
        and report.input_revision == run.input_revision
    )
    if run.mode == "NARRATIVE_REVISION":
        same = same and report.active_narrative_id == run.input_narrative_id
    if not same:
        raise PipelineFailure("INPUT_CHANGED", "Sumber analisis telah berubah. Baca detail terbaru.", 409)


@contextmanager
def locked_run(run_id, token, *, check_input=True):
    report_id = AnalysisRun.objects.values_list("report_id", flat=True).get(pk=run_id)
    with transaction.atomic():
        report = Report.objects.select_for_update().get(pk=report_id)
        run = AnalysisRun.objects.select_for_update().get(pk=run_id)
        ledger = IdempotencyRecord.objects.select_for_update().get(pk=run.request_record_id)
        if (
            run.execution_token != token or ledger.execution_token != token
            or run.status not in ACTIVE or ledger.state not in ACTIVE
        ):
            raise FencedExecution()
        if check_input:
            check_source(report, run)
        yield report, run, ledger


def terminal_ledger(ledger, *, state, status, payload, result_type=None, result_id=None, code=None):
    now = timezone.now()
    ledger.state, ledger.response_status = state, status
    ledger.response_payload = json_value(payload)
    ledger.result_type, ledger.result_id, ledger.error_code = result_type, result_id, code
    ledger.finished_at = now
    ledger.expires_at = now + timedelta(seconds=settings.IDEMPOTENCY_TTL_SECONDS)
    ledger.save()


def fail_run(run_id, token, failure, request_id, *, preserve_failure_code=False):
    with locked_run(run_id, token, check_input=False) as (report, run, ledger):
        try:
            check_source(report, run)
            current = True
        except PipelineFailure:
            current = False
            if not preserve_failure_code:
                failure = PipelineFailure("INPUT_CHANGED", "Sumber analisis sudah berubah.", 409)
        run.status, run.error_code, run.finished_at = "FAILED", failure.error_code, timezone.now()
        run.save()
        if current:
            report.preparation_status, report.blocked_reason = "FAILED", None
        report.revision += 1
        report.save()
        response = {"error": {
            "code": failure.error_code, "message": str(failure.detail),
            "fields": failure.fields, "request_id": str(request_id),
        }}
        terminal_ledger(
            ledger, state="FAILED", status=failure.status_code, payload=response,
            result_type="Run", result_id=run.id, code=failure.error_code,
        )
        record_event(
            actor=None, action="ANALYSIS_FAILED", object_type="AnalysisRun", object_id=run.id,
            report=report, request_id=request_id,
            after={"state": "FAILED", "error_code": failure.error_code, "revision": report.revision},
        )
        return MutationResult(json_value(response), failure.status_code, "Run", run.id)


def persist_stage(run_id, token, stage, result, elapsed, versions):
    with locked_run(run_id, token) as (report, run, ledger):
        identifier = None
        if stage == "WHISPER":
            text, fields = result
            transcript = Transcript.objects.create(
                report=report, analysis_run=run, text=text, **fields
            )
            run.used_transcript = transcript
        elif stage == "NARRATIVE":
            if run.mode == "NARRATIVE_REVISION":
                if result.get("id") != run.input_narrative_id:
                    raise invalid_output()
                narrative = run.input_narrative
            else:
                version = (report.narratives.aggregate(n=Max("version_number"))["n"] or 0) + 1
                narrative = NarrativeVersion.objects.create(
                    report=report, bundle_id=run.bundle_id, producer_run=run,
                    version_number=version, text=result["text"], origin=result["origin"],
                )
            run.output_narrative = narrative
            identifier = narrative.id
        elif stage == "SENA":
            prediction, coverage = result
            SENAResult.objects.create(
                analysis_run=run, narrative_id=run.output_narrative_id,
                category=prediction["label"],
                confidence=Decimal(str(prediction["confidence"])).quantize(
                    Decimal("0.00001"), rounding=ROUND_HALF_UP
                ),
                raw_output=json_value(prediction), model_version=versions["sena"],
            )
            run.execution_context = {**run.execution_context, "sena_token_coverage": json_value(coverage)}
        elif stage == "NARA":
            adapted, coverage, trace = result
            result = adapted["nara_result"]
            NARAResult.objects.create(
                analysis_run=run, narrative_id=run.output_narrative_id,
                raw_output=json_value({
                    **result["raw_output"], "token_coverage": coverage, "postprocessing_trace": trace,
                }),
                normalized_output=json_value(result["normalized_output"]),
                normalization_warnings=json_value(result["normalization_warnings"]),
                model_version=result["model_version"],
            )
        # FUSION stays in memory until the atomic finalization below.
        run.stage = stage
        run.model_versions = json_value(versions)
        run.timings_ms = {**run.timings_ms, stage: elapsed}
        run.save()
        return identifier


def begin_stage(run_id, token, stage):
    with locked_run(run_id, token) as (_, run, _):
        run.stage = stage
        run.save(update_fields=["stage"])


def finalize(run_id, token, fused, request_id, elapsed_total_ms):
    with locked_run(run_id, token) as (report, run, ledger):
        fresh_actor = User.objects.get(pk=ledger.actor_id)
        authorize_analysis(fresh_actor, report)
        require_owner_draft(fresh_actor, report)
        if not run.output_narrative_id or ("A" in run.route and run.mode == "EVIDENCE" and not run.used_transcript_id):
            raise invalid_output()
        sena = SENAResult.objects.get(analysis_run=run, narrative_id=run.output_narrative_id)
        nara = NARAResult.objects.get(analysis_run=run, narrative_id=run.output_narrative_id)
        fields = fused["incident_card_version_fields"]
        validate_card_data(fields["data"])
        expected_data = {
            "event_type": None if sena.category == "NON_EVENT" else sena.category,
            **nara.normalized_output,
        }
        if fields["data"] != expected_data or fields["fusion_version"] != run.model_versions["fusion"]:
            raise invalid_output()
        previous = report.card_versions.order_by("-version_number").first()
        card = IncidentCardVersion.objects.create(
            report=report, bundle_id=run.bundle_id, narrative_id=run.output_narrative_id,
            sena_result=sena, nara_result=nara, parent=previous,
            version_number=previous.version_number + 1 if previous else 1,
            source_kind="AI_FUSION", **fields,
        )
        report.active_narrative_id = run.output_narrative_id
        report.current_card_version = card
        blocked = sena.category == "NON_EVENT"
        report.preparation_status = "BLOCKED" if blocked else "AWAITING_CONFIRMATION"
        report.blocked_reason = "NON_EVENT" if blocked else None
        report.revision += 1
        report.save()
        run.status, run.stage, run.finished_at, run.error_code = "SUCCEEDED", "PERSIST", timezone.now(), None
        run.timings_ms = {**run.timings_ms, "TOTAL": elapsed_total_ms}
        run.save()
        payload = {"data": {
            "report": report_snapshot(report), "result": {"type": "Run", "id": str(run.id)},
            "object": run_data(run), "card_version_id": str(card.id),
        }}
        terminal_ledger(
            ledger, state="SUCCEEDED", status=201, payload=payload,
            result_type="Run", result_id=run.id,
        )
        record_event(
            actor=None, action="ANALYSIS_SUCCEEDED", object_type="AnalysisRun", object_id=run.id,
            report=report, request_id=request_id,
            after={"state": "SUCCEEDED", "revision": report.revision, "card_version_id": str(card.id)},
        )
        result = MutationResult(json_value(payload), 201, "Run", run.id)
    # Exiting the transaction commits the card, pointers, audit and ledger.
    return result


def persistence_uncertain(actor, report_id, key, payload, run_id, token, request_id):
    """Resolve a possibly committed transaction from DB, never from AI in memory."""
    try:
        connection.close_if_unusable_or_obsolete()
        with locked_run(run_id, token, check_input=False) as (report, run, ledger):
            run.status, ledger.state = "UNKNOWN", "UNKNOWN"
            run.save()
            ledger.save()
            report.revision += 1
            report.save()
            record_event(
                actor=None, action="ANALYSIS_UNKNOWN", object_type="AnalysisRun", object_id=run.id,
                report=report, request_id=request_id,
                after={"state": "UNKNOWN", "revision": report.revision},
            )
    except FencedExecution:
        # The final commit may have succeeded before the connection failed.
        fresh = User.objects.get(pk=actor.id)
        report = find_report(fresh, report_id)
        replay = replay_for(fresh, report, key, payload)
        if replay is not None:
            return replay
    except DatabaseError:
        pass  # RUNNING reservation remains protected until technical recovery.
    except AnalysisRun.DoesNotExist:
        # Reservation may not have committed; inference has not started when
        # this occurs at the reservation boundary. Do not invent a result.
        pass
    raise ApiProblem(
        "REQUEST_UNKNOWN", "Hasil penyimpanan belum dapat dipastikan. Baca keadaan tersimpan.", 409
    )


def analyze_report(*, actor, report_id, attrs, key, request_id):
    if connection.in_atomic_block:
        raise RuntimeError("Inference must not run inside a request-wide transaction.")
    key, payload = validate_key(key), canonical_payload(attrs)
    with transaction.atomic():
        actor = User.objects.select_for_update().get(pk=actor.id)
        report = find_report(actor, report_id)
        replay = replay_for(actor, report, key, payload)
        if replay is not None:
            return replay
    require_owner_draft(actor, report)
    if report.revision != attrs["expected_revision"]:
        raise PipelineFailure("REVISION_CONFLICT", "Laporan berubah. Baca detail terbaru.", 409)
    if report.input_revision != attrs["input_revision"] or report.active_bundle_id != attrs["bundle_id"]:
        raise PipelineFailure("INPUT_CHANGED", "Sumber analisis sudah berubah.", 409)
    active = report.analysis_runs.filter(status__in=ACTIVE).first()
    if active:
        raise ApiProblem("REQUEST_" + active.status, "Run sebelumnya belum terminal.", 409)
    bundle = EvidenceBundle.objects.filter(pk=attrs["bundle_id"], report=report).first()
    if bundle is None:
        raise Http404
    original = list(bundle.items.select_related("evidence").order_by("position"))
    route = route_for([member.evidence for member in original])
    narrative = None
    if attrs["mode"] == "NARRATIVE_REVISION":
        narrative = NarrativeVersion.objects.filter(
            pk=attrs["narrative_id"], report=report, bundle=bundle, origin="REPORTER_REVISION"
        ).first()
        if narrative is None or report.active_narrative_id != narrative.id:
            raise PipelineFailure("INPUT_CHANGED", "Narasi revisi bukan sumber aktif.", 409)
    pipeline = get_pipeline(options())
    pipeline.preflight(route, attrs["mode"])
    run = None
    started = time.perf_counter()
    try:
        with analysis_slot() as slot:
            # Serialize reservations for the same actor/key across different
            # reports, while retaining Report -> run -> ledger ordering later.
            with transaction.atomic(durable=True):
                fresh_actor = User.objects.select_for_update().get(pk=actor.id)
                report = Report.objects.select_for_update().get(pk=report_id)
                replay = replay_for(fresh_actor, report, key, payload)
                if replay is not None:
                    return replay
                require_owner_draft(fresh_actor, report)
                if narrative and report.active_narrative_id != narrative.id:
                    raise PipelineFailure("INPUT_CHANGED", "Narasi revisi bukan sumber aktif.", 409)
                if report.blocked_reason:
                    report.blocked_reason = None
                    report.save(update_fields=["blocked_reason"])
                run = create_reserved_run(
                    actor=fresh_actor, report_id=report_id, bundle_id=bundle.id,
                    input_revision=attrs["input_revision"], expected_revision=attrs["expected_revision"],
                    key=key, mode=attrs["mode"], route=route, slot=slot,
                    narrative_id=narrative.id if narrative else None,
                    execution_context={**process_context(), "request_id": str(request_id), "source_digest": bundle.source_digest},
                )
            token = run.execution_token
            # Validate media in the guarded run; decoding does not occur for a
            # narrative revision which only consumes the already stored text.
            begin_stage(run.id, token, "INPUT")
            sources = (
                [EvidenceSource(member.evidence_id, member.evidence.type) for member in original]
                if narrative else load_sources(bundle)
            )
            fused = pipeline.execute(
                sources, existing_narrative=narrative,
                before=lambda stage: begin_stage(run.id, token, stage),
                persist=lambda stage, result, elapsed, versions: persist_stage(
                    run.id, token, stage, result, elapsed, versions
                ),
            )
            return finalize(
                run.id, token, fused, request_id, round((time.perf_counter() - started) * 1000, 3)
            )
    except FencedExecution:
        raise
    except DatabaseError:
        if run is None:
            raise
        return persistence_uncertain(actor, report_id, key, payload, run.id, run.execution_token, request_id)
    except (ApiProblem, Http404, ValidationError, ValueError, TypeError, KeyError) as error:
        if run is None:
            if isinstance(error, ApiProblem) and error.error_code == "CAPACITY_BUSY":
                # A concurrent reservation may have committed after the first
                # replay check. Prefer its authoritative request/run state.
                fresh = User.objects.get(pk=actor.id)
                report = find_report(fresh, report_id)
                replay = replay_for(fresh, report, key, payload)
                if replay is not None:
                    return replay
                active = report.analysis_runs.filter(status__in=ACTIVE).first()
                if active:
                    raise ApiProblem("REQUEST_" + active.status, "Run sebelumnya belum terminal.", 409)
            raise
        failure = error if isinstance(error, ApiProblem) else invalid_output()
        try:
            return fail_run(run.id, run.execution_token, failure, request_id)
        except DatabaseError:
            return persistence_uncertain(actor, report_id, key, payload, run.id, run.execution_token, request_id)
    except Exception as error:
        # No provider messages, prompts, tokens or private text in logs.
        logger.error("analysis_failed run=%s exception_type=%s", getattr(run, "id", None), type(error).__name__)
        if run is None:
            raise
        try:
            return fail_run(run.id, run.execution_token, invalid_output(), request_id)
        except DatabaseError:
            return persistence_uncertain(actor, report_id, key, payload, run.id, run.execution_token, request_id)
