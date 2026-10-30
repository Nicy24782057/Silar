"""Versioned publication; all mutations share the report lock and response ledger.

An allowlisted candidate is private until an assignee explicitly approves and
publishes that exact version. Creating a candidate is not automatic anonymisation.
"""
from copy import deepcopy

from django.http import Http404
from django.utils import timezone

from common.api import ApiProblem
from core.audit import record_event
from core.models import PublicationVersion
from core.mutations import MutationResult, atomic_mutation
from core.notifications import notify
from core.validators import PUBLIC_FIELDS, public_data
from .serializers import publication_data, snapshot
from .workspace_services import active_candidate, handler


def _authorize(actor, report):
    # Current permission and assignment precede replay. Lifecycle checks belong
    # after replay so a completed request can be recovered after later changes.
    handler(actor, report, 'publish_report', allow_closed=True)


def _open(report):
    if report.workflow_status == 'CLOSED':
        raise ApiProblem('TRANSITION_REJECTED', 'Laporan sudah ditutup. Publikasi tidak dapat diubah.', 422)


def _valid_review(report):
    review = report.latest_review
    if (not review or review.outcome != 'VALID' or report.validation_status != 'VALID'
            or review.card_version_id != report.official_card_version_id):
        raise ApiProblem('TRANSITION_REJECTED', 'Publikasi memerlukan review Valid terhadap versi resmi.', 422)


def _audit(actor, report, action, *, version=None, before=None, request_id=None, reason=False):
    after = {'revision': report.revision, 'publication_status': report.publication_status,
             'candidate_id': str(report.active_publication_candidate_id) if report.active_publication_candidate_id else None,
             'published_version_id': str(report.published_version_id) if report.published_version_id else None}
    if version:
        after['state'] = version.state
    if reason:
        after['reason_recorded'] = True
    record_event(actor=actor, report=report, action=action,
                 object_type='PublicationVersion' if version else 'Report',
                 object_id=version.id if version else report.id, before=before, after=after,
                 request_id=request_id,
                 acting_role='OPERATOR' if actor.role == 'ADMIN' else None)


def _result(report, version=None, status=200):
    resource = publication_data(version, internal=True, report=report) if version else snapshot(report)
    kind, object_id = ('Publication', version.id) if version else ('ReportSnapshot', report.id)
    return MutationResult({'report': snapshot(report), 'result': {'type': kind, 'id': str(object_id)},
                           'object': resource}, status, kind, object_id)


def _mutate(actor, report_id, key, data, action, apply):
    return atomic_mutation(actor=actor, report_id=report_id, key=key,
                           scope=f'publication.{action}:{report_id}', payload=data,
                           expected_revision=data['expected_revision'], authorize=_authorize, apply=apply)


def decide(actor, report_id, key, data, request_id=None):
    def apply(user, report):
        _open(report)
        review = report.latest_review
        if not review or review.card_version_id != report.official_card_version_id:
            raise ApiProblem('TRANSITION_REJECTED', 'Review resmi diperlukan sebelum menentukan arah keputusan.', 422)
        if active_candidate(report):
            raise ApiProblem('TRANSITION_REJECTED', 'Batalkan kandidat aktif sebelum mengubah arah keputusan.', 422)
        before = {'publication_status': report.publication_status}
        if data['decision'] == 'INTERNAL':
            if report.published_version_id:
                raise ApiProblem('TRANSITION_REJECTED', 'Versi terbit tetap dipertahankan. Penarikan publikasi tidak tersedia.', 422)
            report.publication_status = 'INTERNAL'
        else:
            _valid_review(report)
            report.publication_status = 'PENDING_APPROVAL'
        report.publication_decision_reason = data['reason']
        report.revision += 1
        report.save(update_fields=['publication_status', 'publication_decision_reason', 'revision'])
        _audit(user, report, 'PUBLICATION_DIRECTION_RECORDED', before=before, request_id=request_id, reason=True)
        return _result(report)
    return _mutate(actor, report_id, key, data, 'decision', apply)


def _initial_data(report, latest):
    if latest:
        result = {name: deepcopy(latest.data.get(name)) for name in PUBLIC_FIELDS}
    else:
        card = report.official_card_version
        source = card.data
        result = {
            'event_type': source.get('event_type'), 'summary': card.narrative.text[:2000],
            'general_location': source.get('location_text'), 'time_text': source.get('time_text'),
            'occurred_at': source.get('occurred_at'),
            'general_impact': '; '.join(source.get('impacts') or [])[:2000] or None,
            'handling_update': None,
        }
    result['event_type'] = report.official_card_version.data.get('event_type')
    return result


def create_candidate(actor, report_id, key, data, request_id=None):
    def apply(user, report):
        _open(report)
        _valid_review(report)
        if report.publication_status != 'PENDING_APPROVAL' or active_candidate(report):
            raise ApiProblem('TRANSITION_REJECTED', 'Siapkan arah publikasi dan pastikan tidak ada kandidat aktif.', 422)
        latest = report.publication_versions.order_by('-version_number').first()
        if data['parent_id'] != (latest.id if latest else None):
            raise ApiProblem('VERSION_CONFLICT', 'Parent harus versi publikasi terakhir, termasuk versi yang dibatalkan.', 409)
        candidate_data = _initial_data(report, latest)
        candidate_data.update(data.get('data', {}))
        # Defence in depth for service callers as well as strict HTTP schemas.
        if set(data.get('data', {})) - (set(PUBLIC_FIELDS) - {'event_type'}):
            raise ApiProblem('INVALID_PAYLOAD', 'Field kandidat tidak diizinkan.', 400)
        public_data(candidate_data)
        version = PublicationVersion(
            report=report, card_version=report.official_card_version, parent=latest,
            version_number=latest.version_number + 1 if latest else 1,
            data=candidate_data, state='DRAFT', sanitized_by=user,
        )
        version.full_clean()
        version.save()
        report.active_publication_candidate = version
        report.revision += 1
        report.save(update_fields=['active_publication_candidate', 'revision'])
        _audit(user, report, 'PUBLICATION_CANDIDATE_CREATED', version=version, request_id=request_id)
        return _result(report, version, 201)
    return _mutate(actor, report_id, key, data, 'create', apply)


def _candidate(report, version_id):
    version = PublicationVersion.objects.select_for_update().filter(pk=version_id, report=report).first()
    if not version:
        raise Http404
    if version.state in ('PUBLISHED', 'CANCELLED'):
        raise ApiProblem('TRANSITION_REJECTED', 'Versi terbit atau dibatalkan bersifat terminal.', 422)
    if report.active_publication_candidate_id != version.id:
        raise ApiProblem('VERSION_CONFLICT', 'Kandidat aktif telah berubah. Muat ulang laporan.', 409)
    return version


def approve_candidate(actor, report_id, key, data, request_id=None, *, version_id):
    def apply(user, report):
        _open(report)
        _valid_review(report)
        version = _candidate(report, version_id)
        if version.state != 'DRAFT':
            raise ApiProblem('TRANSITION_REJECTED', 'Hanya kandidat Draf yang dapat disetujui.', 422)
        public_data(version.data)
        version.state = 'APPROVED'
        version.approved_by = user
        version.approved_at = timezone.now()
        version.save(update_fields=['state', 'approved_by', 'approved_at'])
        report.publication_status = 'APPROVED'
        report.revision += 1
        report.save(update_fields=['publication_status', 'revision'])
        _audit(user, report, 'PUBLICATION_APPROVED', version=version, before={'state': 'DRAFT'}, request_id=request_id)
        return _result(report, version)
    return _mutate(actor, report_id, key, data, f'approve:{version_id}', apply)


def publish_candidate(actor, report_id, key, data, request_id=None, *, version_id):
    def apply(user, report):
        _open(report)
        _valid_review(report)
        version = _candidate(report, version_id)
        if version.state != 'APPROVED' or not version.approved_by_id or not version.approved_at:
            raise ApiProblem('TRANSITION_REJECTED', 'Setujui versi tepat dan sanitasi sebelum menerbitkan.', 422)
        public_data(version.data)
        version.state = 'PUBLISHED'
        version.published_by = user
        version.published_at = timezone.now()
        version.save(update_fields=['state', 'published_by', 'published_at'])
        report.published_version = version
        report.active_publication_candidate = None
        report.publication_status = 'PUBLISHED'
        report.revision += 1
        report.save(update_fields=['published_version', 'active_publication_candidate', 'publication_status', 'revision'])
        _audit(user, report, 'REPORT_PUBLISHED', version=version, before={'state': 'APPROVED'}, request_id=request_id)
        notify(recipient=report.owner, report=report, kind='REPORT_PUBLISHED')
        return _result(report, version)
    return _mutate(actor, report_id, key, data, f'publish:{version_id}', apply)


def cancel_candidate(actor, report_id, key, data, request_id=None, *, version_id):
    def apply(user, report):
        _open(report)
        version = _candidate(report, version_id)
        before = {'state': version.state, 'publication_status': report.publication_status}
        version.state = 'CANCELLED'
        version.cancelled_by = user
        version.cancelled_at = timezone.now()
        version.cancellation_reason = data['reason']
        version.save(update_fields=['state', 'cancelled_by', 'cancelled_at', 'cancellation_reason'])
        report.active_publication_candidate = None
        report.publication_status = 'PUBLISHED' if report.published_version_id else 'NOT_DECIDED'
        report.revision += 1
        report.save(update_fields=['active_publication_candidate', 'publication_status', 'revision'])
        _audit(user, report, 'PUBLICATION_CANCELLED', version=version, before=before, request_id=request_id, reason=True)
        return _result(report, version)
    return _mutate(actor, report_id, key, data, f'cancel:{version_id}', apply)
