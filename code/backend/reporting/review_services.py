"""Short, locked Reporter mutations; model inference remains in SLR11."""
from copy import deepcopy

from django.db.models import Max
from django.utils import timezone

from common.api import ApiProblem
from core.audit import record_event
from core.models import HumanVerification, IncidentCardVersion, NarrativeVersion
from core.mutations import MutationResult, atomic_mutation
from core.notifications import notify
from core.permissions import require_owner_draft
from .serializers import card_data, fields, narrative_data, snapshot
from .services import authorize_owner, envelope


STATE_FIELDS = ('preparation_status', 'workflow_status', 'validation_status', 'publication_status')


def states(report):
    return {key: getattr(report, key) for key in STATE_FIELDS}


def _draft(actor, report):
    require_owner_draft(actor, report)
    if report.workflow_status != 'NOT_SUBMITTED' or report.official_card_version_id:
        raise ApiProblem('TRANSITION_REJECTED', 'Laporan resmi sudah dikunci.', 422)


def _card(report, card_id, *, for_confirmation=False):
    if not report.current_card_version_id or report.current_card_version_id != card_id:
        raise ApiProblem('VERSION_CONFLICT', 'Kartu bukan versi aktif. Baca detail terbaru.', 409)
    card = report.current_card_version
    sena, nara = card.sena_result, card.nara_result
    run = sena.analysis_run
    source_valid = (
        card.report_id == report.id
        and card.bundle_id == report.active_bundle_id
        and card.narrative_id == report.active_narrative_id
        and card.narrative.bundle_id == card.bundle_id
        and sena.narrative_id == card.narrative_id == nara.narrative_id
        and sena.analysis_run_id == nara.analysis_run_id
        and run.report_id == report.id and run.bundle_id == card.bundle_id
        and run.output_narrative_id == card.narrative_id
        and run.input_revision == report.input_revision
        and run.status == 'SUCCEEDED' and run.finished_at is not None
        and run.request_record.report_id == report.id
        and run.request_record.state == 'SUCCEEDED'
        and report.preparation_status in ('AWAITING_CONFIRMATION', 'READY', 'BLOCKED')
        and not report.analysis_runs.filter(status__in=['RUNNING', 'UNKNOWN']).exists()
    )
    if not source_valid:
        raise ApiProblem('SOURCE_CONFLICT', 'Hasil belum lengkap atau sumber telah berubah. Periksa analisis tersimpan.', 409)
    category = sena.category
    if card.data.get('event_type') != (None if category == 'NON_EVENT' else category):
        raise ApiProblem('SOURCE_CONFLICT', 'Kategori kartu tidak sesuai hasil tersimpan.', 409)
    if for_confirmation and category == 'NON_EVENT':
        raise ApiProblem('NON_EVENT', 'Hasil NON_EVENT belum dapat dikonfirmasi atau dikirim. Perbaiki sumber dan analisis ulang.', 422)
    return card


def _mutate(actor, report_id, key, path, data, apply):
    # Replay authorization intentionally permits already-submitted owner reads.
    # Transition guards run only on a new mutation, after the ledger/revision.
    return atomic_mutation(
        actor=actor, key=key, scope=f'POST reports/{report_id}/{path}/', payload=data,
        report_id=report_id, expected_revision=data['expected_revision'],
        authorize=authorize_owner, apply=apply,
    )


def revise_narrative(actor, report_id, key, data, request_id):
    def apply(fresh, report):
        _draft(fresh, report)
        if not report.active_narrative_id or report.active_narrative_id != data['parent_id']:
            raise ApiProblem('VERSION_CONFLICT', 'Narasi bukan versi aktif. Baca detail terbaru.', 409)
        parent = report.active_narrative
        if parent.bundle_id != report.active_bundle_id:
            raise ApiProblem('SOURCE_CONFLICT', 'Sumber narasi telah berubah.', 409)
        before = states(report)
        version = (report.narratives.aggregate(n=Max('version_number'))['n'] or 0) + 1
        narrative = NarrativeVersion.objects.create(
            report=report, bundle=parent.bundle, parent=parent, version_number=version,
            origin='REPORTER_REVISION', text=data['text'], created_by=fresh,
        )
        report.active_narrative = narrative
        report.current_card_version = None
        report.blocked_reason = None
        report.preparation_status = 'DRAFT'
        report.revision += 1
        report.input_revision += 1
        report.save(update_fields=['active_narrative', 'current_card_version', 'blocked_reason',
                                   'preparation_status', 'revision', 'input_revision'])
        record_event(actor=fresh, report=report, action='NARRATIVE_REVISED', object_type='NarrativeVersion',
                     object_id=narrative.id, before=before,
                     after=dict(states(report), revision=report.revision, input_revision=report.input_revision),
                     request_id=request_id)
        return MutationResult(envelope(report, 'Narrative', narrative_data(narrative)), 201, 'Narrative', narrative.id)
    return _mutate(actor, report_id, key, 'narratives/revisions', data, apply)


def revise_card(actor, report_id, key, data, request_id):
    def apply(fresh, report):
        _draft(fresh, report)
        parent = _card(report, data['parent_id'])
        before = states(report)
        values = deepcopy(parent.data)
        values.update(data['patch'])
        version = (report.card_versions.aggregate(n=Max('version_number'))['n'] or 0) + 1
        card = IncidentCardVersion.objects.create(
            report=report, bundle=parent.bundle, narrative=parent.narrative,
            sena_result=parent.sena_result, nara_result=parent.nara_result,
            parent=parent, version_number=version, source_kind='REPORTER_FIELD_REVISION',
            data=values, uncertain=parent.uncertain, uncertain_reasons=deepcopy(parent.uncertain_reasons),
            fusion_version=parent.fusion_version, created_by=fresh,
        )
        report.current_card_version = card
        non_event = parent.sena_result.category == 'NON_EVENT'
        report.preparation_status = 'BLOCKED' if non_event else 'AWAITING_CONFIRMATION'
        report.blocked_reason = 'NON_EVENT' if non_event else None
        report.revision += 1
        report.save(update_fields=['current_card_version', 'preparation_status', 'blocked_reason', 'revision'])
        record_event(actor=fresh, report=report, action='CARD_REVISED', object_type='IncidentCardVersion', object_id=card.id,
                     before=before, after=dict(states(report), card_version_id=str(card.id), revision=report.revision,
                     changed_fields=sorted(data['patch'])), request_id=request_id)
        return MutationResult(envelope(report, 'Card', card_data(card)), 201, 'Card', card.id)
    return _mutate(actor, report_id, key, 'cards/revisions', data, apply)


def verification_data(obj):
    return fields(obj, 'id created_at report_id card_version_id reporter_id confirmed_at')


def confirm_card(actor, report_id, key, data, request_id):
    def apply(fresh, report):
        _draft(fresh, report)
        card = _card(report, data['card_version_id'], for_confirmation=True)
        previous = HumanVerification.objects.filter(report=report, card_version=card, reporter=fresh).first()
        if previous:
            return MutationResult(envelope(report, 'Verification', verification_data(previous)), 200, 'Verification', previous.id)
        before = states(report)
        verification = HumanVerification.objects.create(
            report=report, card_version=card, reporter=fresh, confirmed_at=timezone.now(),
        )
        report.preparation_status = 'READY'
        report.blocked_reason = None
        report.revision += 1
        report.save(update_fields=['preparation_status', 'blocked_reason', 'revision'])
        record_event(actor=fresh, report=report, action='HUMAN_VERIFIED', object_type='HumanVerification', object_id=verification.id,
                     before=before, after=dict(states(report), card_version_id=str(card.id), revision=report.revision), request_id=request_id)
        return MutationResult(envelope(report, 'Verification', verification_data(verification)), 201, 'Verification', verification.id)
    return _mutate(actor, report_id, key, 'human-verifications', data, apply)


def submit_card(actor, report_id, key, data, request_id):
    def apply(fresh, report):
        _draft(fresh, report)
        card = _card(report, data['card_version_id'], for_confirmation=True)
        if report.preparation_status != 'READY' or not HumanVerification.objects.filter(
            report=report, card_version=card, reporter=fresh,
        ).exists():
            raise ApiProblem('VERIFICATION_REQUIRED', 'Konfirmasi versi aktif diperlukan sebelum mengirim.', 422)
        before = states(report)
        report.official_card_version = card
        report.submitted_at = timezone.now()
        report.workflow_status = 'SUBMITTED'
        report.revision += 1
        report.save(update_fields=['official_card_version', 'submitted_at', 'workflow_status', 'revision'])
        record_event(actor=fresh, report=report, action='REPORT_SUBMITTED', object_type='Report', object_id=report.id,
                     before=before, after=dict(states(report), card_version_id=str(card.id), revision=report.revision), request_id=request_id)
        notify(recipient=fresh, report=report, kind='REPORT_SUBMITTED')
        return MutationResult(envelope(report, 'ReportSnapshot', snapshot(report)), 200, 'ReportSnapshot', report.id)
    return _mutate(actor, report_id, key, 'submit', data, apply)
