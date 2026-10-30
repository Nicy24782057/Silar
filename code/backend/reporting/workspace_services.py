"""SLR13 operations on the existing official-report aggregate.

No schema changes, model execution or publication-candidate creation occurs here.
All writes share the SLR08 revision, idempotency, audit and notification services.
"""
from dataclasses import replace

from django.db import transaction, DatabaseError
from django.http import Http404
from django.utils import timezone
from accounts.models import User
from common.api import ApiProblem
from core.audit import record_event
from core.models import OperatorAssignment, OperatorReview, FollowUpRecord, PublicationVersion
from core.mutations import atomic_mutation, MutationResult
from core.notifications import notify
from core.permissions import effective_permissions, require_admin, require_operator, is_assignee
from .serializers import snapshot


def staff(actor):
    if actor.role not in ('OPERATOR', 'ADMIN') or not actor.is_active or not actor.email_verified_at:
        raise ApiProblem('PERMISSION_DENIED', 'Ruang kerja memerlukan akun petugas aktif.', 403)


def official(report):
    if not report or not report.submitted_at or not report.official_card_version_id:
        raise Http404


def handler(actor, report, permission, *, allow_closed=False):
    official(report)
    require_operator(actor, permission)
    if not is_assignee(actor, report):
        raise Http404
    if not allow_closed and report.workflow_status == 'CLOSED':
        raise ApiProblem('TRANSITION_REJECTED', 'Laporan sudah ditutup. Perubahan tidak diizinkan.', 422)


def active_candidate(report):
    return bool(report.active_publication_candidate_id or
                PublicationVersion.objects.filter(report=report, state__in=['DRAFT', 'APPROVED']).exists())


def close_requirements(report):
    review = report.latest_review
    return [
        {'key': 'review', 'label': 'Review resmi yang sah sudah tersedia',
         'met': bool(review and review.card_version_id == report.official_card_version_id)},
        {'key': 'followups', 'label': 'Seluruh tindak lanjut selesai atau dibatalkan',
         'met': not report.followups.filter(status='PENDING').exists()},
        {'key': 'publication', 'label': 'Status publikasi Internal atau Terbit',
         'met': report.publication_status in ('INTERNAL', 'PUBLISHED')},
        {'key': 'candidate', 'label': 'Tidak ada kandidat publikasi aktif', 'met': not active_candidate(report)},
    ]


def recipients(report, *, old_operator=None):
    ids = {report.owner_id}
    current = report.assignments.filter(ended_at__isnull=True).first()
    if current:
        ids.add(current.operator_id)
    if old_operator:
        ids.add(old_operator)
    return User.objects.filter(id__in=ids, is_active=True, email_verified_at__isnull=False)


def events(actor, report, action, kind, *, object_type='Report', object_id=None, before=None, after=None,
           request_id=None, old_operator=None, acting_operator=False):
    values = {'revision': report.revision, 'workflow_status': report.workflow_status,
              'validation_status': report.validation_status, 'publication_status': report.publication_status}
    values.update(after or {})
    record_event(actor=actor, action=action, object_type=object_type, object_id=object_id or report.id,
                 report=report, before=before, after=values, request_id=request_id,
                 acting_role='OPERATOR' if acting_operator and actor.role == 'ADMIN' else None)
    for user in recipients(report, old_operator=old_operator):
        notify(recipient=user, report=report, kind=kind)
    # The acting Admin receives the same metadata-only event, with no duplicate.
    if actor.role == 'ADMIN' and actor.id not in {u.id for u in recipients(report, old_operator=old_operator)}:
        notify(recipient=actor, report=report, kind=kind)


def mutate(actor, report_id, key, data, action, authorize, apply):
    return atomic_mutation(actor=actor, key=key, scope=f'workspace.{action}:{report_id}', payload=data,
                           report_id=report_id, expected_revision=data['expected_revision'],
                           authorize=authorize, apply=apply)


def claim(actor, report_id, key, data, request_id=None):
    def authorize(user, report):
        official(report)
        require_operator(user, 'claim_report')
        if 'view_queue' not in effective_permissions(user):
            raise ApiProblem('PERMISSION_DENIED', 'Izin antrean diperlukan untuk klaim.', 403)
        if report.workflow_status == 'CLOSED':
            raise ApiProblem('TRANSITION_REJECTED', 'Laporan sudah ditutup.', 422)
        current = report.assignments.filter(ended_at__isnull=True).first()
        if current and current.operator_id != user.id:
            raise ApiProblem('ALREADY_CLAIMED', 'Laporan sudah diklaim petugas lain. Muat ulang antrean.', 409)

    def apply(user, report):
        if report.workflow_status != 'SUBMITTED' or report.assignments.filter(ended_at__isnull=True).exists():
            raise ApiProblem('ALREADY_CLAIMED', 'Laporan sudah memiliki penanggung jawab.', 409)
        assignment = OperatorAssignment.objects.create(report=report, operator=user, assigned_by=user,
                                                       source='SELF_CLAIM', started_at=timezone.now())
        report.workflow_status = 'ASSIGNED'; report.revision += 1; report.save()
        events(user, report, 'REPORT_CLAIMED', 'REPORT_ASSIGNED',
               after={'assignment_id': str(assignment.id), 'operator_id': str(user.id)}, request_id=request_id,
               acting_operator=True)
        return MutationResult({'report': snapshot(report), 'message': 'Laporan berhasil diklaim.'})
    return mutate(actor, report_id, key, data, 'claim', authorize, apply)


def assign(actor, report_id, key, data, request_id=None):
    def authorize(user, report):
        require_admin(user, 'assign_report'); official(report)
        if report.workflow_status == 'CLOSED':
            raise ApiProblem('TRANSITION_REJECTED', 'Penugasan laporan yang ditutup tidak dapat diubah.', 422)

    def apply(user, report):
        # Never wait for a target who is already performing another locked operation.
        try:
            with transaction.atomic():
                target = User.objects.select_for_update(nowait=True).filter(pk=data['operator_id']).first()
        except DatabaseError:
            raise ApiProblem('TARGET_BUSY', 'Petugas sedang memperbarui data. Muat ulang sebelum menugaskan.', 409)
        if (not target or target.role not in ('OPERATOR', 'ADMIN') or not target.is_active or
                not target.email_verified_at or 'view_assigned_report' not in effective_permissions(target)):
            raise ApiProblem('INVALID_ASSIGNEE', 'Pilih petugas aktif, terverifikasi, dan memiliki izin membaca tugas.', 422)
        current = report.assignments.filter(ended_at__isnull=True).first()
        old_id = current.operator_id if current else None
        if old_id == target.id:
            raise ApiProblem('TRANSITION_REJECTED', 'Petugas ini sudah menjadi penanggung jawab.', 422)
        now = timezone.now()
        if current:
            current.ended_at = now; current.save(update_fields=['ended_at'])
        assignment = OperatorAssignment.objects.create(report=report, operator=target, assigned_by=user,
            source='ADMIN_REASSIGNMENT' if current else 'ADMIN_ASSIGNMENT', started_at=now, reason=data['reason'])
        if report.workflow_status == 'SUBMITTED': report.workflow_status = 'ASSIGNED'
        report.revision += 1; report.save()
        events(user, report, 'REPORT_REASSIGNED' if current else 'REPORT_ASSIGNED', 'REPORT_ASSIGNED',
            before={'operator_id': str(old_id) if old_id else None},
            after={'operator_id': str(target.id), 'assignment_id': str(assignment.id), 'reason_recorded': True},
            request_id=request_id, old_operator=old_id)
        return MutationResult({'report': snapshot(report), 'message': 'Penanggung jawab berhasil diperbarui.'})
    return mutate(actor, report_id, key, data, 'assign', authorize, apply)


def review(actor, report_id, key, data, request_id=None):
    def authorize(user, report): handler(user, report, 'review_report')

    def apply(user, report):
        if report.published_version_id or report.publication_status in ('PUBLISHED', 'APPROVED') or active_candidate(report):
            raise ApiProblem('TRANSITION_REJECTED', 'Review dikunci selama ada kandidat aktif atau publikasi terbit.', 422)
        assignment = report.assignments.get(ended_at__isnull=True)
        result = OperatorReview.objects.create(report=report, card_version=report.official_card_version,
            assignment=assignment, operator=user, outcome=data['outcome'], reason=data['reason'], reviewed_at=timezone.now())
        report.latest_review = result; report.validation_status = result.outcome
        report.workflow_status = 'FOLLOW_UP' if report.followups.filter(status='PENDING').exists() else 'IN_REVIEW'
        # A new review requires a fresh publication-direction decision.
        report.publication_status = 'NOT_DECIDED' if result.outcome == 'VALID' else 'INTERNAL'
        report.publication_decision_reason = None; report.revision += 1; report.save()
        events(user, report, 'REVIEW_RECORDED', 'REVIEW_RECORDED', object_type='OperatorReview', object_id=result.id,
               after={'outcome': result.outcome, 'card_version_id': str(result.card_version_id),
                      'reason_recorded': True}, request_id=request_id, acting_operator=True)
        return MutationResult({'report': snapshot(report), 'message': 'Review resmi berhasil disimpan.'}, 201)
    return mutate(actor, report_id, key, data, 'review', authorize, apply)


def followup(actor, report_id, key, data, request_id=None, followup_id=None):
    def authorize(user, report): handler(user, report, 'manage_followup')

    def apply(user, report):
        if not report.latest_review_id:
            raise ApiProblem('TRANSITION_REJECTED', 'Catat review resmi sebelum membuat tindak lanjut.', 422)
        if followup_id:
            record = FollowUpRecord.objects.select_for_update().filter(pk=followup_id, report=report).first()
            if not record: raise Http404
            if record.status != 'PENDING':
                raise ApiProblem('TRANSITION_REJECTED', 'Tindak lanjut ini sudah selesai atau dibatalkan.', 422)
            record.status = data['status']; record.completion_reason = data['completion_reason']
            record.finished_at = timezone.now(); record.save()
        else:
            record = FollowUpRecord.objects.create(report=report, assignment=report.assignments.get(ended_at__isnull=True),
                                                   operator=user, description=data['description'])
        report.workflow_status = 'FOLLOW_UP' if report.followups.filter(status='PENDING').exists() else 'IN_REVIEW'
        report.revision += 1; report.save()
        events(user, report, 'FOLLOW_UP_UPDATED', 'FOLLOW_UP_UPDATED', object_type='FollowUpRecord', object_id=record.id,
               after={'status': record.status, 'reason_recorded': bool(record.completion_reason)}, request_id=request_id,
               acting_operator=True)
        return MutationResult({'report': snapshot(report), 'message': 'Tindak lanjut berhasil disimpan.'}, 200 if followup_id else 201)
    return mutate(actor, report_id, key, data, 'followup.' + str(followup_id or 'new'), authorize, apply)


def decide(actor, report_id, key, data, request_id=None):
    # Retain the SLR13 workspace URL while sharing the canonical SLR14 guards,
    # replacement flow and idempotent response with publication-decision/.
    from .publication_services import decide as publication_decide
    result = publication_decide(actor, report_id, key, data, request_id)
    # Keep the SLR13 response shape for existing clients. The ledger stores the
    # canonical response, so replay through either URL retains the same result.
    message = (
        'Arah persiapan publikasi dicatat. Laporan belum terbit; penerbitan memerlukan proses persetujuan publikasi.'
        if data['decision'] == 'PREPARE' else 'Keputusan internal berhasil disimpan.')
    if data['decision'] == 'PREPARE' and result.payload['report']['published_version_id']:
        message = 'Persiapan versi pengganti dicatat. Versi terbit lama tetap tersedia sampai penggantinya diterbitkan.'
    return replace(result, payload={'report': result.payload['report'], 'message': message})


def close(actor, report_id, key, data, request_id=None):
    def authorize(user, report): handler(user, report, 'close_report', allow_closed=True)

    def apply(user, report):
        if report.workflow_status == 'CLOSED':
            raise ApiProblem('TRANSITION_REJECTED', 'Laporan ini sudah ditutup.', 422)
        missing = [item['label'] for item in close_requirements(report) if not item['met']]
        if missing:
            raise ApiProblem('CLOSE_REQUIREMENTS', 'Persyaratan penutupan belum terpenuhi.', 422, {'requirements': missing})
        report.workflow_status = 'CLOSED'; report.closed_at = timezone.now(); report.closed_by = user
        report.closure_note = data['closure_note']; report.revision += 1; report.save()
        events(user, report, 'REPORT_CLOSED', 'REPORT_CLOSED', after={'reason_recorded': True},
               request_id=request_id, acting_operator=True)
        return MutationResult({'report': snapshot(report), 'message': 'Laporan berhasil ditutup. Riwayat tetap dapat dibaca.'})
    return mutate(actor, report_id, key, data, 'close', authorize, apply)
