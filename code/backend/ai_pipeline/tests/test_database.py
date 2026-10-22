"""Requires real PostgreSQL 16, including the existing immutable-history triggers.

Neural/provider clients are explicit test doubles. These tests verify transaction
and HTTP behavior, not the quality of SENA/NARA/Whisper/Gemini predictions.
"""
import hashlib
import json
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
import uuid

from django.db import DatabaseError, connection, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from common.testing import user
from core.capacity import analysis_slot
from core.models import (
    AnalysisRun, AuditEvent, EvidenceBundle, EvidenceBundleItem, EvidenceItem,
    HumanVerification, IdempotencyRecord, IncidentCardVersion,
    NarrativeVersion, NARAResult, Report, SENAResult,
)
from ai_pipeline.errors import PipelineFailure
from ai_pipeline.recovery import abort_stopped
from ai_pipeline.services import terminal_ledger
from ai_pipeline.tests.test_components import FakeRuntime, empty_fields, prediction


class ControlledRuntime(FakeRuntime):
    def __init__(self):
        super().__init__()
        self.label = "FLOOD"
        self.confidence = 0.98
        self.before_fusion = None

    def sena(self, text):
        self.calls.append(("SENA", text))
        return prediction(self.label, self.confidence), {"truncated": False}

    def fuse(self, adapted):
        if self.before_fusion:
            self.before_fusion()
        self.calls.append(("FUSION", None))
        return {"incident_card_version_fields": {
            "data": {"event_type": None if self.label == "NON_EVENT" else self.label, **empty_fields()},
            "uncertain": self.confidence < 0.95,
            "uncertain_reasons": ["LOW_CLASSIFICATION_CONFIDENCE"] if self.confidence < 0.95 else [],
            "fusion_version": "fixture-fusion",
        }}


class AnalysisDatabaseTests(TransactionTestCase):
    reset_sequences = False

    def setUp(self):
        if connection.vendor != "postgresql":
            raise RuntimeError("Run this suite with real PostgreSQL 16.")
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version_num")
            if int(cursor.fetchone()[0]) // 10000 != 16:
                raise RuntimeError("PostgreSQL major 16 is required.")
        self.owner = user()
        self.other = user("other@example.test")
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(PRIVATE_MEDIA_ROOT=Path(self.media.name))
        override.enable()
        self.addCleanup(override.disable)
        self.runtime = ControlledRuntime()
        self.runtime_patch = patch("ai_pipeline.pipeline.reviewed_runtime", return_value=self.runtime)
        self.runtime_patch.start()
        self.addCleanup(self.runtime_patch.stop)
        self.whisper = MagicMock(version="fixture-whisper")
        self.whisper.transcribe.return_value = "Air meluap."
        self.whisper_patch = patch("ai_pipeline.pipeline.whisper_client", return_value=self.whisper)
        self.whisper_patch.start()
        self.addCleanup(self.whisper_patch.stop)
        self.gemini = MagicMock()
        self.gemini.narrative.return_value = ("Air terlihat menggenang.", {"resolved_model": "fixture-gemini"})
        self.gemini_patch = patch("ai_pipeline.pipeline.GeminiClient", return_value=self.gemini)
        self.gemini_patch.start()
        self.addCleanup(self.gemini_patch.stop)
        self.report, self.bundle = self.source()
        self.body = {
            "mode": "EVIDENCE", "bundle_id": str(self.bundle.id),
            "input_revision": self.report.input_revision, "expected_revision": self.report.revision,
        }
        self.key = uuid.uuid4()

    def source(self, channels="T"):
        report = Report.objects.create(owner=self.owner)
        items = []
        for channel in channels:
            if channel == "T":
                text = "Air meluap di Jalan Melati."
                data = text.encode("utf-8")
                extra = {"type": "TEXT", "text_content": text}
            else:
                if channel == "A":
                    data = (Path(__file__).parent / "fixtures" / "tone.wav").read_bytes()
                    filename, mime, kind = "tone.wav", "audio/wav", "AUDIO"
                else:
                    from PIL import Image
                    image = BytesIO()
                    Image.new("RGB", (8, 8), color="blue").save(image, format="JPEG")
                    data, filename, mime, kind = image.getvalue(), "image.jpg", "image/jpeg", "IMAGE"
                key = "evidence/" + uuid.uuid4().hex
                target = Path(self.media.name) / key
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                extra = {"type": kind, "file_key": key, "original_name": filename, "mime_type": mime}
            items.append(EvidenceItem.objects.create(
                report=report, uploaded_by=self.owner, byte_size=len(data),
                sha256=hashlib.sha256(data).hexdigest(), **extra,
            ))
        with transaction.atomic():
            bundle = EvidenceBundle.objects.create(
                report=report, created_by=self.owner, version_number=1, source_digest="a" * 64
            )
            for position, item in enumerate(items, 1):
                EvidenceBundleItem.objects.create(bundle=bundle, evidence=item, position=position)
        report.active_bundle = bundle
        report.save()
        return report, bundle

    def post(self, body=None, key=None, report=None):
        report = report or self.report
        return self.client.post(
            f"/api/v1/reports/{report.id}/analyses/",
            body if body is not None else self.body, format="json",
            HTTP_IDEMPOTENCY_KEY=str(key if key is not None else self.key),
        )

    def test_success_commits_card_ledger_and_audit_before_http_success(self):
        committed = []
        actual = terminal_ledger

        def track(*args, **kwargs):
            result = actual(*args, **kwargs)
            transaction.on_commit(lambda: committed.append(True))
            return result

        with patch("ai_pipeline.services.terminal_ledger", side_effect=track):
            response = self.post()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(committed)
        self.assertFalse(connection.in_atomic_block)
        self.report.refresh_from_db()
        self.assertEqual(self.report.preparation_status, "AWAITING_CONFIRMATION")
        self.assertIsNone(self.report.official_card_version_id)
        self.assertFalse(HumanVerification.objects.exists())
        self.assertEqual(IdempotencyRecord.objects.get(key=self.key).state, "SUCCEEDED")
        self.assertEqual(IncidentCardVersion.objects.count(), 1)
        self.assertEqual(response.data["data"]["card_version_id"], str(self.report.current_card_version_id))
        self.assertTrue(AuditEvent.objects.filter(action="ANALYSIS_SUCCEEDED").exists())

    def test_all_seven_routes_persist_sources_and_audio_reference(self):
        for channels in ["T", "A", "I", "TA", "TI", "AI", "TAI"]:
            with self.subTest(channels=channels):
                report, bundle = self.source(channels)
                body = {"mode": "EVIDENCE", "bundle_id": str(bundle.id), "input_revision": 1, "expected_revision": 1}
                response = self.post(body, uuid.uuid4(), report)
                self.assertEqual(response.status_code, 201)
                run = report.analysis_runs.get()
                self.assertEqual(run.route, channels)
                self.assertEqual(run.used_transcript_id is not None, "A" in channels)
                self.assertEqual(run.sena_result.narrative_id, run.nara_result.narrative_id)
                self.assertEqual(run.output_narrative_id, run.sena_result.narrative_id)

    def test_terminal_replay_has_no_new_inference_or_revision(self):
        first = self.post()
        self.assertEqual(first.status_code, 201)
        self.report.refresh_from_db()
        revision, calls, audits = self.report.revision, len(self.runtime.calls), AuditEvent.objects.count()
        replay = self.post()
        self.assertEqual(replay.data, first.data)
        self.assertEqual(replay["Idempotency-Replayed"], "true")
        self.report.refresh_from_db()
        self.assertEqual(self.report.revision, revision)
        self.assertEqual(len(self.runtime.calls), calls)
        self.assertEqual(AuditEvent.objects.count(), audits)

    def test_replay_does_not_reapply_submitted_transition_guard(self):
        first = self.post()
        self.report.refresh_from_db()
        card = self.report.current_card_version
        HumanVerification.objects.create(
            report=self.report, card_version=card, reporter=self.owner, confirmed_at=timezone.now()
        )
        self.report.official_card_version = card
        self.report.preparation_status = "READY"
        self.report.workflow_status = "SUBMITTED"
        self.report.submitted_at = timezone.now()
        self.report.save()
        replay = self.post()
        self.assertEqual(replay.status_code, 201)
        self.assertEqual(replay.data, first.data)

    def test_replay_checks_current_account_before_returning_snapshot(self):
        self.post()
        type(self.owner).objects.filter(pk=self.owner.id).update(is_active=False)
        response = self.post()
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("data", response.data)

    def test_same_key_with_new_revision_is_mismatch(self):
        self.post()
        self.report.refresh_from_db()
        response = self.post({**self.body, "expected_revision": self.report.revision})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"]["code"], "IDEMPOTENCY_MISMATCH")

    def test_other_owner_cannot_start_or_read_run(self):
        response = self.post()
        run_id = response.data["data"]["object"]["id"]
        self.client.force_authenticate(self.other)
        self.assertEqual(self.post(key=uuid.uuid4()).status_code, 404)
        response = self.client.get(f"/api/v1/reports/{self.report.id}/analysis-runs/{run_id}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/requests/{self.key}/").status_code, 404)

    def test_capacity_full_does_not_mutate_report(self):
        with analysis_slot():
            response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"]["code"], "CAPACITY_BUSY")
        self.report.refresh_from_db()
        self.assertEqual(self.report.revision, 1)
        self.assertEqual(self.report.preparation_status, "DRAFT")
        self.assertFalse(AnalysisRun.objects.exists())

    def test_source_change_preserves_partial_history_but_never_activates_old_card(self):
        def change_source():
            with transaction.atomic():
                report = Report.objects.select_for_update().get(pk=self.report.id)
                report.input_revision += 1
                report.revision += 1
                report.preparation_status = "DRAFT"
                report.current_card_version = None
                report.save()

        self.runtime.before_fusion = change_source
        response = self.post()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"]["code"], "INPUT_CHANGED")
        self.report.refresh_from_db()
        self.assertEqual(self.report.preparation_status, "DRAFT")
        self.assertIsNone(self.report.current_card_version_id)
        self.assertTrue(SENAResult.objects.exists())
        self.assertTrue(NARAResult.objects.exists())
        self.assertFalse(IncidentCardVersion.objects.exists())

    def test_non_event_is_blocked_and_empty_fields_do_not_make_uncertain(self):
        self.runtime.label = "NON_EVENT"
        response = self.post()
        self.assertEqual(response.status_code, 201)
        self.report.refresh_from_db()
        card = self.report.current_card_version
        self.assertEqual(self.report.preparation_status, "BLOCKED")
        self.assertIsNone(card.data["event_type"])
        self.assertFalse(card.uncertain)
        self.assertEqual(card.data["victims"], [])

    def test_known_upstream_failure_keeps_partial_narrative_and_safe_error(self):
        self.runtime.sena = MagicMock(side_effect=PipelineFailure(
            "AI_UPSTREAM_FAILED", "Layanan belum dapat digunakan.", 502
        ))
        response = self.post()
        self.assertEqual(response.status_code, 502)
        run = AnalysisRun.objects.get()
        self.assertEqual(run.status, "FAILED")
        self.assertIsNotNone(run.output_narrative_id)
        self.assertFalse(IncidentCardVersion.objects.exists())
        self.assertNotIn("execution_context", json.dumps(response.data))

    def test_finalization_error_rolls_back_card_and_never_returns_success(self):
        actual = terminal_ledger

        def reject_success(*args, **kwargs):
            if kwargs["state"] == "SUCCEEDED":
                raise ValueError("simulated failure after card insert")
            return actual(*args, **kwargs)

        with patch("ai_pipeline.services.terminal_ledger", side_effect=reject_success):
            response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertFalse(IncidentCardVersion.objects.exists())
        self.assertEqual(AnalysisRun.objects.get().status, "FAILED")
        self.assertEqual(IdempotencyRecord.objects.get().state, "FAILED")
        self.assertFalse(AuditEvent.objects.filter(action="ANALYSIS_SUCCEEDED").exists())

    def test_uncertain_database_outcome_keeps_slot_and_get_is_read_only(self):
        with patch("ai_pipeline.services.finalize", side_effect=DatabaseError("simulated database uncertainty")):
            response = self.post()
        self.assertEqual(response.status_code, 409)
        run = AnalysisRun.objects.get()
        self.assertEqual(run.status, "UNKNOWN")
        self.assertEqual(IdempotencyRecord.objects.get().state, "UNKNOWN")
        self.report.refresh_from_db()
        revision, audits = self.report.revision, AuditEvent.objects.count()
        for url in [
            "/api/v1/requests/", f"/api/v1/requests/{self.key}/",
            f"/api/v1/reports/{self.report.id}/analysis-runs/{run.id}/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.report.refresh_from_db(); run.refresh_from_db()
        self.assertEqual(self.report.revision, revision)
        self.assertEqual(run.status, "UNKNOWN")
        self.assertEqual(AuditEvent.objects.count(), audits)
        retry = self.post(
            {**self.body, "expected_revision": self.report.revision}, key=uuid.uuid4()
        )
        self.assertEqual(retry.data["error"]["code"], "REQUEST_UNKNOWN")

    def test_recovery_refuses_live_process_then_fences_old_token_after_proof(self):
        with patch("ai_pipeline.services.finalize", side_effect=DatabaseError("simulated")):
            self.post()
        run = AnalysisRun.objects.get()
        old_token = run.execution_token
        with self.assertRaises(ValueError):
            abort_stopped(run.id, old_token)
        run.refresh_from_db()
        self.assertEqual(run.execution_token, old_token)
        # Only the process-observation boundary is replaced. Transaction,
        # token replacement, audit, and source guards run against PostgreSQL.
        with patch("ai_pipeline.recovery.stopped_process_evidence", return_value="PROCESS_NOT_PRESENT"):
            abort_stopped(run.id, old_token)
        run.refresh_from_db()
        self.assertEqual(run.status, "FAILED")
        self.assertEqual(run.error_code, "RECOVERY_ABORTED")
        self.assertNotEqual(run.execution_token, old_token)
        from ai_pipeline.services import begin_stage
        from ai_pipeline.errors import FencedExecution
        with self.assertRaises(FencedExecution):
            begin_stage(run.id, old_token, "NARA")

    def test_narrative_revision_reuses_narrative_without_transcription(self):
        report, bundle = self.source("AI")
        narrative = NarrativeVersion.objects.create(
            report=report, bundle=bundle, version_number=1,
            text="Narasi revisi Reporter.", origin="REPORTER_REVISION", created_by=self.owner,
        )
        report.active_narrative = narrative
        report.save()
        body = {
            "mode": "NARRATIVE_REVISION", "bundle_id": str(bundle.id), "narrative_id": str(narrative.id),
            "input_revision": 1, "expected_revision": 1,
        }
        response = self.post(body, uuid.uuid4(), report)
        self.assertEqual(response.status_code, 201)
        run = report.analysis_runs.get()
        self.assertEqual(run.input_narrative_id, narrative.id)
        self.assertEqual(run.output_narrative_id, narrative.id)
        self.assertIsNone(run.used_transcript_id)
        self.whisper.transcribe.assert_not_called()
        self.gemini.narrative.assert_not_called()
        self.assertEqual(report.narratives.count(), 1)
