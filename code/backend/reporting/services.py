from datetime import timedelta
import json
import uuid
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.utils import timezone
from accounts.models import User
from common.api import ApiProblem
from core.audit import record_event
from core.models import Report, EvidenceItem, EvidenceBundle, EvidenceBundleItem, IdempotencyRecord
from core.mutations import atomic_mutation, MutationResult, request_digest
from core.permissions import require_report_read, require_owner_draft
from core.storage import PrivateMediaStorage, store_validated_media
from .media import BUNDLE_LIMIT
from .serializers import snapshot, evidence_data, bundle_data


def require_reporter(actor):
    if not actor.is_active or not actor.email_verified_at or actor.role != 'REPORTER':
        raise ApiProblem('PERMISSION_DENIED', 'Akun Reporter aktif dan terverifikasi diperlukan.', 403)


def authorize_owner(actor, report):
    require_reporter(actor)
    require_report_read(actor, report, content=True)


def delete_draft(actor, report_id, key, expected_revision, request_id):
    def authorize(fresh, report):
        require_reporter(fresh)
        if report.owner_id!=fresh.id:
            raise Http404

    def apply(fresh, report):
        if report.deleted_at is not None:
            raise Http404
        if report.submitted_at or report.workflow_status!='NOT_SUBMITTED' or report.official_card_version_id:
            raise ApiProblem('TRANSITION_REJECTED','Laporan yang sudah dikirim tidak dapat dihapus.',422)
        if report.analysis_runs.filter(status__in=['RUNNING','UNKNOWN']).exists():
            raise ApiProblem('ANALYSIS_IN_PROGRESS','Pastikan hasil analisis yang masih berjalan atau belum pasti sebelum menghapus laporan.',409)
        before={'revision':report.revision,'workflow_status':report.workflow_status}
        report.deleted_at=timezone.now();report.deleted_by=fresh;report.revision+=1
        report.save(update_fields=['deleted_at','deleted_by','revision'])
        record_event(actor=fresh,action='REPORT_DELETED',object_type='Report',object_id=report.id,report=report,
                     before=before,after={'revision':report.revision,'deleted_at':report.deleted_at.isoformat()},request_id=request_id)
        return MutationResult({'id':str(report.id),'revision':report.revision,'deleted_at':report.deleted_at.isoformat()},200,'Report',report.id)

    return atomic_mutation(actor=actor,key=key,scope=f'DELETE reports/{report_id}/',
        payload={'expected_revision':expected_revision},report_id=report_id,expected_revision=expected_revision,
        authorize=authorize,apply=apply)


def envelope(report, kind, obj):
    return {'report': snapshot(report), 'result': {'type': kind, 'id': obj['id']}, 'object': obj}


def create_report(actor, key, request_id):
    try:
        key = uuid.UUID(str(key))
    except (ValueError, TypeError):
        raise ApiProblem('INVALID_PAYLOAD', 'Idempotency-Key harus UUID.', 400)
    digest = request_digest({})
    with transaction.atomic():
        actor = User.objects.select_for_update().get(pk=actor.pk)
        require_reporter(actor)
        record = IdempotencyRecord.objects.select_for_update().filter(actor=actor, key=key).first()
        if record:
            if record.scope != 'reports.create' or record.request_hash != digest:
                raise ApiProblem('IDEMPOTENCY_MISMATCH', 'Key dipakai untuk tindakan berbeda.', 409)
            if record.report_id:
                require_report_read(actor, record.report, content=True)
            if record.state in ('RUNNING', 'UNKNOWN'):
                raise ApiProblem('REQUEST_' + record.state, 'Hasil request sebelumnya belum terminal.', 409)
            if not record.expires_at or record.expires_at <= timezone.now() or record.response_payload is None:
                raise ApiProblem('IDEMPOTENCY_EXPIRED', 'Masa replay habis. Baca kembali daftar draft.', 409)
            return MutationResult(record.response_payload, record.response_status, 'ReportSnapshot', record.result_id, True)
        report = Report.objects.create(owner=actor)
        obj = snapshot(report)
        payload = envelope(report, 'ReportSnapshot', obj)
        record = IdempotencyRecord.objects.create(actor=actor, report=report, key=key, scope='reports.create',
            request_hash=digest, state='SUCCEEDED', result_type='ReportSnapshot', result_id=report.id,
            response_status=201, response_payload=payload, finished_at=timezone.now(),
            expires_at=timezone.now() + timedelta(seconds=settings.IDEMPOTENCY_TTL_SECONDS))
        record_event(actor=actor, action='REPORT_CREATED', object_type='Report', object_id=report.id,
                     report=report, after={'revision': 1, 'input_revision': 1}, request_id=request_id)
        return MutationResult(payload, 201, 'ReportSnapshot', report.id)


def upload_evidence(actor, report_id, key, metadata, raw, expected_revision, request_id):
    payload = {k: v for k, v in metadata.items() if k != 'file_key'}
    payload['expected_revision'] = expected_revision
    saved_keys = []

    def apply(fresh_actor, report):
        require_owner_draft(fresh_actor, report)
        values = dict(metadata)
        if metadata['type'] != 'TEXT':
            values['file_key'] = store_validated_media(ContentFile(raw))
            saved_keys.append(values['file_key'])
        item = EvidenceItem.objects.create(report=report, uploaded_by=fresh_actor, **values)
        report.revision += 1
        report.save(update_fields=['revision'])
        record_event(actor=fresh_actor, action='EVIDENCE_UPLOADED', object_type='EvidenceItem', object_id=item.id,
                     report=report, after={'revision': report.revision, 'input_revision': report.input_revision}, request_id=request_id)
        return MutationResult(envelope(report, 'Evidence', evidence_data(item)), 201, 'EvidenceItem', item.id)

    try:
        return atomic_mutation(actor=actor, key=key, scope='evidence.upload', payload=payload,
            report_id=report_id, expected_revision=expected_revision, authorize=authorize_owner, apply=apply)
    except Exception:
        storage = PrivateMediaStorage()
        for name in saved_keys:
            storage.delete(name)
        raise


def create_bundle(actor, report_id, key, evidence_ids, expected_revision, request_id):
    payload = {'evidence_ids': [str(x) for x in evidence_ids], 'expected_revision': expected_revision}

    def apply(fresh_actor, report):
        require_owner_draft(fresh_actor, report)
        rows = {x.id: x for x in EvidenceItem.objects.filter(report=report, id__in=evidence_ids)}
        if len(rows) != len(evidence_ids):
            raise ApiProblem('INVALID_PAYLOAD', 'Semua bukti harus berasal dari draft yang sama.', 400)
        items = [rows[x] for x in evidence_ids]
        types = [x.type for x in items]
        if types.count('TEXT') > 1 or types.count('AUDIO') > 1 or types.count('IMAGE') > 3:
            raise ApiProblem('INVALID_PAYLOAD', 'Bundle maksimal satu teks, satu audio, dan tiga gambar.', 400)
        if sum(x.byte_size for x in items) > BUNDLE_LIMIT:
            raise ApiProblem('INPUT_TOO_LARGE', 'Total bukti terpilih maksimal 25 MiB termasuk teks.', 413)
        version = (report.bundles.aggregate(number=Max('version_number'))['number'] or 0) + 1
        digest = request_digest({'items': [{'type': x.type, 'id': str(x.id), 'sha256': x.sha256, 'position': i}
                                          for i, x in enumerate(items, 1)]})
        bundle = EvidenceBundle.objects.create(report=report, version_number=version, source_digest=digest, created_by=fresh_actor)
        for position, item in enumerate(items, 1):
            EvidenceBundleItem.objects.create(bundle=bundle, evidence=item, position=position)
        report.active_bundle = bundle
        report.active_narrative = None
        report.current_card_version = None
        report.blocked_reason = None
        report.preparation_status = 'DRAFT'
        report.revision += 1
        report.input_revision += 1
        report.save(update_fields=['active_bundle', 'active_narrative', 'current_card_version', 'blocked_reason',
                                   'preparation_status', 'revision', 'input_revision'])
        record_event(actor=fresh_actor, action='BUNDLE_CREATED', object_type='EvidenceBundle', object_id=bundle.id,
            report=report, after={'revision': report.revision, 'input_revision': report.input_revision,
            'bundle_id': str(bundle.id), 'preparation_status': 'DRAFT'}, request_id=request_id)
        return MutationResult(envelope(report, 'Bundle', bundle_data(bundle)), 201, 'EvidenceBundle', bundle.id)

    return atomic_mutation(actor=actor, key=key, scope='bundles.create', payload=payload, report_id=report_id,
                           expected_revision=expected_revision, authorize=authorize_owner, apply=apply)
