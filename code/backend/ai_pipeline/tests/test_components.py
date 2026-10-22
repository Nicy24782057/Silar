from dataclasses import replace
from datetime import timedelta
from io import BytesIO
import json
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import uuid
import wave
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from ai_pipeline.audio import decode_audio
from ai_pipeline.clients import GeminiClient
from ai_pipeline.config import options
from ai_pipeline.errors import PipelineFailure
from ai_pipeline.execution import process_context, stopped_process_evidence
from ai_pipeline.narrative import normalize
from ai_pipeline.output import request_data, run_data
from ai_pipeline.pipeline import Pipeline
from ai_pipeline.runtime import active_modules, safe_service_metadata
from ai_pipeline.serializers import AnalysisCreate
from ai_pipeline.sources import EvidenceSource, load_sources, route_for, validate_image
from ai_pipeline.views import AnalysisView

FIXTURES = Path(__file__).parent / "fixtures"


def empty_fields():
    return {
        "location_text": None, "time_text": None, "occurred_at": None,
        "involved_parties": [], "impacts": [], "victims": [], "affected_objects": [],
    }


def prediction(label="FLOOD", confidence=0.98):
    labels = ["FLOOD", "EARTHQUAKE", "FIRE", "ACCIDENT", "NON_EVENT"]
    return {
        "label": label, "confidence": confidence,
        "probabilities": {name: confidence if name == label else (1 - confidence) / 4 for name in labels},
    }


class FakeRuntime:
    """Deterministic dependency only; never installed as a production runtime."""
    versions = {"sena": "fixture-sena", "nara": "fixture-nara", "fusion": "fixture-fusion"}

    def __init__(self):
        self.calls = []

    def sena(self, text):
        self.calls.append(("SENA", text))
        return prediction(), {"truncated": False}

    def nara(self, text, narrative_id, sena):
        self.calls.append(("NARA", text))
        return {
            "nara_result": {
                "normalized_output": empty_fields(), "raw_output": {},
                "normalization_warnings": [], "model_version": "fixture-nara",
            }
        }, {}, {}

    def fuse(self, adapted):
        self.calls.append(("FUSION", None))
        return {"incident_card_version_fields": {
            "data": {"event_type": "FLOOD", **empty_fields()},
            "uncertain": False, "uncertain_reasons": [], "fusion_version": "fixture-fusion",
        }}


class RoutingAndNormalizerTests(SimpleTestCase):
    def test_all_seven_original_channel_routes(self):
        for route in ["T", "A", "I", "TA", "TI", "AI", "TAI"]:
            with self.subTest(route=route):
                mapping = {"T": "TEXT", "A": "AUDIO", "I": "IMAGE"}
                self.assertEqual(route_for([EvidenceSource(uuid.uuid4(), mapping[x]) for x in route]), route)

    def test_multiple_images_are_one_original_channel(self):
        self.assertEqual(route_for([EvidenceSource(uuid.uuid4(), "IMAGE") for _ in range(3)]), "I")

    def test_invalid_counts_are_rejected(self):
        for items in [[], ["TEXT", "TEXT"], ["AUDIO", "AUDIO"], ["IMAGE"] * 4, ["VIDEO"]]:
            with self.subTest(items=items), self.assertRaises(PipelineFailure):
                route_for([EvidenceSource(uuid.uuid4(), item) for item in items])

    def test_normalizer_preserves_facts_case_negation_and_punctuation(self):
        self.assertEqual(
            normalize("  TIDAK   ada korban.\r\nJl. Melati, pukul\t07.30.\n\n\nBelum   surut.  "),
            "TIDAK ada korban.\nJl. Melati, pukul 07.30.\n\nBelum surut.",
        )

    def test_normalizer_rejects_empty_control_and_excessive_output(self):
        for value in [" ", "Banjir\x00terjadi", "x" * 10001, None]:
            with self.subTest(value=str(value)[:25]), self.assertRaises(PipelineFailure):
                normalize(value)

    @override_settings(AI_CPU_THREADS="0")
    def test_invalid_ai_config_does_not_prevent_auth_url_loading(self):
        self.assertEqual(resolve("/api/v1/auth/login/").func.view_class.__name__, "LoginView")
        with self.assertRaises(PipelineFailure) as raised:
            options()
        self.assertEqual(raised.exception.error_code, "AI_CONFIGURATION_NOT_READY")

    def test_api_key_is_not_in_options_repr(self):
        with override_settings(GEMINI_API_KEY="private-test-key"):
            self.assertNotIn("private-test-key", repr(options()))


class AudioBoundaryTests(SimpleTestCase):
    def test_real_decoding_of_all_four_target_formats(self):
        for filename, mime in [
            ("tone.mp3", "audio/mpeg"), ("tone.wav", "audio/wav"),
            ("tone.webm", "audio/webm;codecs=opus"), ("tone.m4a", "audio/mp4"),
        ]:
            with self.subTest(filename=filename):
                decoded = decode_audio((FIXTURES / filename).read_bytes(), filename, mime)
                self.assertEqual(decoded.samples.ndim, 1)
                self.assertGreater(decoded.duration_ms, 0)
                self.assertLess(decoded.duration_ms, 1000)
                self.assertEqual(str(decoded.samples.dtype), "float32")

    def test_renaming_webm_as_mp3_is_rejected(self):
        with self.assertRaises(PipelineFailure) as raised:
            decode_audio((FIXTURES / "tone.webm").read_bytes(), "renamed.mp3", "audio/mpeg")
        self.assertEqual(raised.exception.error_code, "MEDIA_UNSUPPORTED")

    def test_declared_mime_does_not_override_decoded_content(self):
        with self.assertRaises(PipelineFailure):
            decode_audio((FIXTURES / "tone.wav").read_bytes(), "tone.wav", "audio/mpeg")

    def test_broken_audio_is_rejected(self):
        with self.assertRaises(PipelineFailure):
            decode_audio(b"not audio", "fake.mp3", "audio/mpeg")

    def test_decoded_duration_limit_is_enforced(self):
        data = BytesIO()
        with wave.open(data, "wb") as output:
            output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000)
            output.writeframes(b"\0\0" * (121 * 16000))
        with self.assertRaises(PipelineFailure) as raised:
            decode_audio(data.getvalue(), "long.wav", "audio/wav")
        self.assertEqual(raised.exception.error_code, "INPUT_TOO_LARGE")


class PipelineRouteTests(SimpleTestCase):
    def run_route(self, route, revision=False):
        runtime = FakeRuntime()
        decoded = SimpleNamespace(samples=[], duration_ms=1000)
        mapping = {"T": "TEXT", "A": "AUDIO", "I": "IMAGE"}
        sources = [
            EvidenceSource(uuid.uuid4(), mapping[item], text="Banjir di Jalan Melati.",
                           data=b"image", mime_type="image/jpeg", audio=decoded)
            for item in route
        ]
        narrative = SimpleNamespace(id=uuid.uuid4(), text="Narasi revisi Reporter.") if revision else None
        stages, persisted = [], []
        narrative_id = narrative.id if narrative else uuid.uuid4()
        whisper = SimpleNamespace(version="fixture-whisper", transcribe=MagicMock(return_value="Air meluap."))
        gemini = MagicMock()
        gemini.narrative.return_value = ("Narasi dari bukti.", {"requested_model": "fixture-gemini"})

        def persist(stage, result, elapsed, versions):
            persisted.append(stage)
            return narrative_id if stage == "NARRATIVE" else None

        with patch("ai_pipeline.pipeline.reviewed_runtime", return_value=runtime), \
             patch("ai_pipeline.pipeline.whisper_client", return_value=whisper), \
             patch("ai_pipeline.pipeline.GeminiClient", return_value=gemini):
            pipeline = Pipeline(options())
            pipeline.preflight(route, "NARRATIVE_REVISION" if revision else "EVIDENCE")
            result = pipeline.execute(sources, existing_narrative=narrative, before=stages.append, persist=persist)
        return result, runtime, stages, whisper, gemini

    def test_seven_routes_call_only_required_components(self):
        for route in ["T", "A", "I", "TA", "TI", "AI", "TAI"]:
            with self.subTest(route=route):
                _, runtime, stages, whisper, gemini = self.run_route(route)
                self.assertEqual(whisper.transcribe.call_count, int("A" in route))
                self.assertEqual(gemini.narrative.call_count, int("I" in route or len(route) > 1))
                self.assertEqual([name for name, _ in runtime.calls], ["SENA", "NARA", "FUSION"])
                self.assertEqual(runtime.calls[0][1], runtime.calls[1][1])
                self.assertEqual(stages[-1], "PERSIST")

    def test_narrative_revision_never_calls_whisper_or_gemini(self):
        _, runtime, _, whisper, gemini = self.run_route("TAI", revision=True)
        whisper.transcribe.assert_not_called()
        gemini.narrative.assert_not_called()
        self.assertEqual(runtime.calls[0][1], "Narasi revisi Reporter.")

    def test_audio_transcript_does_not_trigger_gemini(self):
        _, runtime, _, whisper, gemini = self.run_route("A")
        gemini.narrative.assert_not_called()
        self.assertEqual(runtime.calls[0][1], "Air meluap.")


class AdapterRuleTests(SimpleTestCase):
    def test_reviewed_fusion_threshold_and_non_event_rules(self):
        _, adapter, historical = active_modules(options().slr09_root)
        text = "Air meluap di jalan."
        tokens = [
            {"token": match.group().lower(), "original": match.group(),
             "start": match.start(), "end": match.end(), "label": "O", "confidence": 1.0}
            for match in historical.TOKEN_PATTERN.finditer(text)
        ]
        for label, confidence, uncertain, blocked in [
            ("FLOOD", 0.95, False, False),
            ("FLOOD", 0.94999, True, False),
            ("NON_EVENT", 0.99, False, True),
        ]:
            with self.subTest(label=label, confidence=confidence):
                raw, _ = historical.build_adapter_input(text, prediction(label, confidence), tokens)
                adapted = adapter.adapt_legacy_ai_output(
                    raw, narrative_id=str(uuid.uuid4()),
                    sena_model_version="fixture-sena", nara_model_version="fixture-nara",
                )
                fused = adapter.fuse_for_silar(
                    adapted, confidence_threshold=0.95, calibration_reference="unit-test-operational-cutoff"
                )
                card = fused["incident_card_version_fields"]
                self.assertEqual(card["uncertain"], uncertain)
                self.assertEqual(fused["integration_signals"]["blocked_by_non_event"], blocked)
                self.assertEqual(card["data"]["event_type"], None if blocked else "FLOOD")
                self.assertEqual(card["data"]["victims"], [])
                self.assertIsNone(card["data"]["occurred_at"])


class GeminiBoundaryTests(SimpleTestCase):
    def test_payload_contains_only_relevant_text_transcript_and_images(self):
        sources = [
            EvidenceSource(uuid.uuid4(), "TEXT", text="Tidak ada korban."),
            EvidenceSource(uuid.uuid4(), "AUDIO", data=b"RAW_AUDIO_MUST_NOT_BE_SENT"),
            EvidenceSource(uuid.uuid4(), "IMAGE", data=b"image", mime_type="image/jpeg"),
        ]
        evidence, images = GeminiClient.evidence_payload(sources, "Air meluap.")
        self.assertEqual(set(evidence), {"teks_reporter", "transkrip_audio"})
        self.assertEqual(images, [("image/jpeg", b"image")])
        self.assertNotIn("RAW_AUDIO", repr((evidence, images)))
        self.assertNotIn(str(sources[0].evidence_id), repr((evidence, images)))

    def call_gemini(self, text, finish="STOP"):
        from google.genai import types
        response = types.GenerateContentResponse(
            candidates=[types.Candidate(
                finish_reason=finish,
                content=types.Content(parts=[types.Part.from_text(text=text)]),
            )],
            model_version="fixture-gemini-resolved",
        )
        client = MagicMock()
        client.models.generate_content.return_value = response
        manager = MagicMock()
        manager.__enter__.return_value = client
        config = replace(options(), gemini_key="fixture-private-key")
        with patch("google.genai.Client", return_value=manager) as factory:
            result = GeminiClient(config).narrative(
                [EvidenceSource(uuid.uuid4(), "IMAGE", data=b"image", mime_type="image/jpeg")], None, 5000
            )
        return result, factory, client

    def test_sdk_receives_bounded_single_attempt_and_structured_narrative(self):
        (narrative, metadata), factory, client = self.call_gemini('{"narrative":"Air terlihat menggenang."}')
        self.assertEqual(narrative, "Air terlihat menggenang.")
        self.assertEqual(metadata["resolved_model"], "fixture-gemini-resolved")
        self.assertEqual(factory.call_args.kwargs["http_options"].retry_options.attempts, 1)
        self.assertEqual(factory.call_args.kwargs["http_options"].timeout, 5000)
        config = client.models.generate_content.call_args.kwargs["config"]
        self.assertEqual(config.response_json_schema["required"], ["narrative"])
        self.assertEqual(config.tools, [])
        self.assertNotIn("fixture-private-key", str(client.models.generate_content.call_args))

    def test_extra_classification_fields_and_truncated_output_are_rejected(self):
        for text, finish in [
            ('{"narrative":"Air.","event_type":"FLOOD"}', "STOP"),
            ('{"narrative":""}', "STOP"),
            ('{"narrative":"Air."}', "MAX_TOKENS"),
            ("not json", "STOP"),
        ]:
            with self.subTest(finish=finish, text=text), self.assertRaises(PipelineFailure):
                self.call_gemini(text, finish)

    @override_settings(GEMINI_API_KEY="")
    def test_missing_key_is_an_explicit_configuration_failure(self):
        with self.assertRaises(PipelineFailure) as raised:
            GeminiClient(options())
        self.assertEqual(raised.exception.error_code, "AI_CONFIGURATION_NOT_READY")


class ContractAndRecoveryTests(SimpleTestCase):
    def test_service_metadata_is_configuration_only_and_contains_no_secrets(self):
        with override_settings(GEMINI_API_KEY="private-test-key"), \
             patch("ai_pipeline.runtime.reviewed_runtime", return_value=FakeRuntime()), \
             patch("ai_pipeline.clients.verified_whisper_manifest", return_value={"revision": "a" * 40}):
            result = safe_service_metadata()
        self.assertEqual(set(result), {"models", "configuration_present", "capacity_limit"})
        self.assertTrue(result["configuration_present"]["gemini"])
        self.assertNotIn("private-test-key", json.dumps(result))
        self.assertNotIn("READY", json.dumps(result))

    def test_analysis_schema_rejects_unknown_fields_boolean_revision_and_wrong_mode(self):
        valid = {"mode": "EVIDENCE", "bundle_id": str(uuid.uuid4()), "input_revision": 1, "expected_revision": 1}
        for changes in [
            {"category": "FLOOD"}, {"expected_revision": True},
            {"mode": "NARRATIVE_REVISION"}, {"narrative_id": str(uuid.uuid4())},
        ]:
            with self.subTest(changes=changes):
                self.assertFalse(AnalysisCreate(data={**valid, **changes}).is_valid())

    def test_post_returns_the_saved_snapshot_and_replay_header(self):
        from core.mutations import MutationResult
        request = APIRequestFactory().post(
            "/api/v1/reports/" + str(uuid.uuid4()) + "/analyses/",
            {"mode": "EVIDENCE", "bundle_id": str(uuid.uuid4()), "input_revision": 1, "expected_revision": 1},
            format="json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        request.request_id = uuid.uuid4()
        force_authenticate(request, user=SimpleNamespace(
            is_authenticated=True, is_active=True, email_verified_at=timezone.now()
        ))
        snapshot = {"data": {"result": {"type": "Run", "id": str(uuid.uuid4())}}}
        with patch("ai_pipeline.views.analyze_report", return_value=MutationResult(snapshot, 201, replayed=True)) as call:
            response = AnalysisView.as_view()(request, report_id=uuid.uuid4())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, snapshot)
        self.assertEqual(response["Idempotency-Replayed"], "true")
        call.assert_called_once()

    def test_request_metadata_never_serializes_private_response_or_execution_context(self):
        now = timezone.now()
        record = SimpleNamespace(
            key=uuid.uuid4(), scope="POST reports/example/analyses/", state="SUCCEEDED",
            report_id=uuid.uuid4(), result_type="Run", result_id=uuid.uuid4(),
            response_status=201, error_code=None, created_at=now, finished_at=now,
            expires_at=now + timedelta(hours=1), response_payload={"private": "never expose"},
            execution_token=uuid.uuid4(), execution_context={"pid": 123},
        )
        result = request_data(record)
        self.assertEqual(set(result), {
            "key", "scope", "state", "report_id", "result_type", "result_id", "response_status",
            "error_code", "created_at", "finished_at", "expires_at", "replay_available",
        })
        self.assertTrue(result["replay_available"])
        self.assertNotIn("never expose", json.dumps(result))

    def test_live_process_is_not_proof_for_aborting_an_unknown_run(self):
        with self.assertRaises(ValueError):
            stopped_process_evidence(process_context())

    def test_another_host_is_not_accepted_as_local_process_proof(self):
        with self.assertRaises(ValueError):
            stopped_process_evidence({"host": socket.gethostname() + "-other", "pid": 99, "process_started_at": 1})

    def test_run_monitor_projection_does_not_expose_private_content_or_execution_identity(self):
        now = timezone.now()
        run = SimpleNamespace(
            id=uuid.uuid4(), created_at=now, report_id=uuid.uuid4(), bundle_id=uuid.uuid4(),
            input_narrative_id=None, output_narrative_id=uuid.uuid4(), used_transcript_id=uuid.uuid4(),
            input_revision=1, mode="EVIDENCE", route="AI", status="RUNNING", stage="NARA",
            model_versions={"sena": "fixture-sena"}, started_at=now, finished_at=None,
            error_code=None, timings_ms={"WHISPER": 1000},
            execution_context={"pid": 123}, execution_token=uuid.uuid4(), capacity_slot=1,
        )
        result = run_data(run, content=False)
        for field in ["used_transcript", "output_narrative", "sena", "nara"]:
            self.assertIsNone(result[field])
        for field in ["execution_context", "execution_token", "capacity_slot", "request_hash"]:
            self.assertNotIn(field, result)


class SourceBoundaryTests(SimpleTestCase):
    def test_changed_text_hash_is_rejected(self):
        import hashlib
        report_id = uuid.uuid4()
        evidence = SimpleNamespace(
            id=uuid.uuid4(), report_id=report_id, type="TEXT", text_content="Air meluap.",
            byte_size=len("Air meluap.".encode()), sha256=hashlib.sha256(b"different content").hexdigest(),
        )
        members = MagicMock()
        members.select_related.return_value.order_by.return_value = [SimpleNamespace(evidence=evidence)]
        bundle = SimpleNamespace(report_id=report_id, items=members)
        with self.assertRaises(PipelineFailure) as raised:
            load_sources(bundle)
        self.assertEqual(raised.exception.error_code, "MEDIA_UNSUPPORTED")

    def test_media_path_cannot_escape_private_root(self):
        report_id = uuid.uuid4()
        evidence = SimpleNamespace(
            id=uuid.uuid4(), report_id=report_id, type="AUDIO", file_key="../outside.wav",
        )
        members = MagicMock()
        members.select_related.return_value.order_by.return_value = [SimpleNamespace(evidence=evidence)]
        with TemporaryDirectory() as directory, override_settings(PRIVATE_MEDIA_ROOT=Path(directory) / "private"):
            (Path(directory) / "private").mkdir()
            (Path(directory) / "outside.wav").write_bytes((FIXTURES / "tone.wav").read_bytes())
            with self.assertRaises(PipelineFailure) as raised:
                load_sources(SimpleNamespace(report_id=report_id, items=members))
        self.assertEqual(raised.exception.error_code, "MEDIA_UNSUPPORTED")

    def test_png_signature_and_full_decode_are_checked(self):
        from PIL import Image
        data = BytesIO()
        Image.new("RGB", (8, 8), color="blue").save(data, format="PNG")
        self.assertEqual(validate_image(data.getvalue(), "image.png", "image/png"), "image/png")
        with self.assertRaises(PipelineFailure):
            validate_image(data.getvalue(), "image.jpg", "image/jpeg")
        with self.assertRaises(PipelineFailure):
            validate_image(b"broken", "image.png", "image/png")
