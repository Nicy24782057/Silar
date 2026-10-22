import uuid

from django.db import transaction

from core.audit import record_event

from .errors import PipelineFailure
from .execution import stopped_process_evidence
from .services import fail_run, locked_run


def mark_unknown(run_id, expected_token, request_id=None):
    request_id = request_id or uuid.uuid4()
    with locked_run(run_id, expected_token, check_input=False) as (report, run, ledger):
        if run.status == "UNKNOWN" and ledger.state == "UNKNOWN":
            return run
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
        return run


def abort_stopped(run_id, expected_token, request_id=None):
    """OS proof and fencing are required; no Admin HTTP retry operation exists."""
    request_id = request_id or uuid.uuid4()
    # The proof is rechecked while holding Report/run/ledger locks.
    with transaction.atomic():
        with locked_run(run_id, expected_token, check_input=False) as (report, run, ledger):
            evidence = stopped_process_evidence(run.execution_context)
            replacement = uuid.uuid4()
            run.execution_token = ledger.execution_token = replacement
            run.execution_context = {**run.execution_context, "recovery_evidence": evidence}
            run.save()
            ledger.save()
            # Nested short transaction uses the new token, preventing old writers.
            result = fail_run(
                run.id, replacement,
                PipelineFailure("RECOVERY_ABORTED", "Analisis dihentikan melalui pemulihan teknis.", 503),
                request_id,
                preserve_failure_code=True,
            )
            record_event(
                actor=None, action="ANALYSIS_RECOVERY_ABORTED", object_type="AnalysisRun",
                object_id=run.id, report=report, request_id=request_id,
                after={"state": "FAILED", "error_code": "RECOVERY_ABORTED"},
            )
        return result
