"""Publication contract, privacy and lifecycle; concurrency needs PostgreSQL 16."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch
from uuid import uuid4

from django.core.management import call_command
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from common.testing import user
from core.models import (AuditEvent, HumanVerification, IncidentCardVersion, Notification,
                         IdempotencyRecord, OperatorAssignment, OperatorReview, PublicationVersion)
from core.permissions import ADMIN_PERMISSIONS, OPERATOR_PERMISSIONS
from core.test_fixtures import source_chain
from core.validators import PUBLIC_FIELDS


def reviewed_report(owner, operator):
    report, bundle, run, card, evidence = source_chain(owner, official=True)
    assignment = OperatorAssignment.objects.create(report=report, operator=operator, assigned_by=operator,
                                                    source='SELF_CLAIM', started_at=timezone.now())
    review = OperatorReview.objects.create(report=report, card_version=card, assignment=assignment,
                                           operator=operator, outcome='VALID', reason='Sesuai sumber resmi.',
                                           reviewed_at=timezone.now())
    report.latest_review = review
    report.validation_status = 'VALID'
    report.workflow_status = 'IN_REVIEW'
    report.save()
    return report, card


class PublicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_silar', verbosity=0)
        cls.owner = user('reporter-private@example.test')
        cls.operator = user('publisher@example.test', role='OPERATOR', perms=OPERATOR_PERMISSIONS)
        cls.other = user('other-operator@example.test', role='OPERATOR', perms=OPERATOR_PERMISSIONS)
        cls.admin = user('administrator@example.test', role='ADMIN', perms=ADMIN_PERMISSIONS)
        cls.report, cls.card = reviewed_report(cls.owner, cls.operator)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.operator)

    def post(self, action, body=None, *, version=None, key=None, revision=None, actor=None):
        if actor:
            self.client.force_authenticate(user=actor)
        self.report.refresh_from_db()
        data = {'expected_revision': self.report.revision if revision is None else revision, **(body or {})}
        suffix = 'publication-decision/' if action == 'decision' else 'publication-versions/'
        if version:
            suffix += f'{version}/{action}/'
        return self.client.post(f'/api/v1/reports/{self.report.id}/{suffix}', data, format='json',
                                HTTP_IDEMPOTENCY_KEY=str(key or uuid4()))

    def prepare(self):
        response = self.post('decision', {'decision': 'PREPARE', 'reason': 'Siapkan informasi publik.'})
        self.assertEqual(response.status_code, 200, response.content)
        return response

    def candidate(self, values=None, parent=None):
        self.prepare()
        response = self.post('create', {'parent_id': parent, 'data': values or {}})
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()['data']['object']

    def publish(self, values=None, parent=None):
        candidate = self.candidate(values, parent)
        approved = self.post('approve', version=candidate['id'])
        self.assertEqual(approved.status_code, 200, approved.content)
        response = self.post('publish', version=candidate['id'])
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()['data']['object']

    def public(self, path=''):
        return APIClient().get('/api/v1/public/reports/' + path)

    def test_prepare_and_candidates_are_not_public_and_publish_requires_exact_approval(self):
        self.prepare()
        self.assertFalse(PublicationVersion.objects.exists())
        created = self.post('create', {'parent_id': None})
        self.assertEqual(created.status_code, 201, created.content)
        payload = created.json()['data']
        self.assertEqual(set(payload), {'report', 'result', 'object'})
        self.assertEqual(payload['result']['type'], 'Publication')
        candidate = payload['object']
        self.assertEqual(candidate['state'], 'DRAFT')
        self.assertEqual(self.public().json()['count'], 0)
        self.assertEqual(self.public(f'{self.report.id}/').status_code, 404)
        self.assertEqual(self.post('publish', version=candidate['id']).status_code, 422)
        self.assertEqual(self.post('approve', version=candidate['id']).status_code, 200)
        self.assertEqual(self.public().json()['count'], 0)
        self.assertEqual(self.post('publish', version=candidate['id']).status_code, 200)
        data = self.public(f'{self.report.id}/').json()['data']
        self.assertEqual(set(data), {'id', 'published_at', *PUBLIC_FIELDS})
        self.assertEqual(data['id'], str(self.report.id))
        self.assertEqual(data['event_type'], 'FLOOD')
        self.assertIsNotNone(data['published_at'])
        self.report.refresh_from_db()
        self.assertEqual(self.report.workflow_status, 'IN_REVIEW')
        self.assertIsNone(self.report.active_publication_candidate_id)
        self.assertEqual(Notification.objects.filter(kind='REPORT_PUBLISHED', report=self.report).count(), 1)
        self.assertEqual(Notification.objects.get(kind='REPORT_PUBLISHED').recipient_id, self.owner.id)

    def test_workspace_decision_preserves_slr13_response_and_replays_canonical_ledger(self):
        key = str(uuid4())
        body = {'decision': 'PREPARE', 'reason': 'Persiapan melalui workspace.',
                'expected_revision': self.report.revision}
        path = f'/api/v1/workspace/reports/{self.report.id}/decision/'
        response = self.client.post(path, body, format='json', HTTP_IDEMPOTENCY_KEY=key)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(set(response.json()['data']), {'report', 'message'})
        replay = self.client.post(path, body, format='json', HTTP_IDEMPOTENCY_KEY=key)
        self.assertEqual(replay.json(), response.json())
        canonical = self.post('decision', {'decision': body['decision'], 'reason': body['reason']},
                              key=key, revision=body['expected_revision'])
        self.assertEqual(canonical.status_code, 200, canonical.content)
        self.assertEqual(set(canonical.json()['data']), {'report', 'result', 'object'})
        self.assertEqual(AuditEvent.objects.filter(report=self.report, action='PUBLICATION_DIRECTION_RECORDED').count(), 1)

    def test_schema_rejects_unknown_fields_category_override_naive_time_and_missing_parent(self):
        self.prepare()
        for values in [{'event_type': 'FIRE'}, {'victims': ['private']}, {'summary': ''},
                       {'summary': None}, {'occurred_at': '2026-10-29T08:00:00'},
                       {'summary': 'x' * 2001}, {'general_location': 'x' * 501}]:
            response = self.post('create', {'parent_id': None, 'data': values})
            self.assertEqual(response.status_code, 400, (values, response.content))
        self.assertEqual(self.post('create', {'data': {}}).status_code, 400)
        self.assertEqual(self.post('create', {'parent_id': None, 'unexpected': True}).status_code, 400)
        self.assertFalse(PublicationVersion.objects.exists())

    def test_aware_timestamp_is_normalized_to_utc_and_unknown_values_stay_null(self):
        version = self.publish({'occurred_at': '2026-10-29T15:00:00+07:00', 'general_location': None,
                                'time_text': None, 'general_impact': None, 'handling_update': None})
        self.assertEqual(version['data']['occurred_at'], '2026-10-29T08:00:00Z')
        result = self.public(f'{self.report.id}/').json()['data']
        for name in ['general_location', 'time_text', 'general_impact', 'handling_update']:
            self.assertIsNone(result[name])

    def test_owner_other_operator_admin_without_operator_grants_cannot_mutate(self):
        for actor, code in [(self.owner, 403), (self.other, 404), (self.admin, 403)]:
            self.assertEqual(self.post('decision', {'decision': 'PREPARE', 'reason': 'Tidak sah.'},
                                       actor=actor).status_code, code)
        self.assertFalse(PublicationVersion.objects.exists())

    def test_no_candidate_for_invalid_review_or_closed_report(self):
        self.report.validation_status = 'INVALID'
        self.report.save(update_fields=['validation_status'])
        self.assertEqual(self.post('decision', {'decision': 'PREPARE', 'reason': 'Tidak sah.'}).status_code, 422)
        self.report.workflow_status = 'CLOSED'; self.report.closed_at = timezone.now()
        self.report.closed_by = self.operator; self.report.closure_note = 'Ditutup untuk uji guard.'
        self.report.save(update_fields=['workflow_status', 'closed_at', 'closed_by', 'closure_note'])
        self.assertEqual(self.post('create', {'parent_id': None}).status_code, 422)

    def test_first_cancellation_restores_not_decided_and_latest_cancelled_parent_is_required(self):
        first = self.candidate({'summary': 'Ringkasan pertama.'})
        self.assertEqual(self.post('cancel', {'reason': 'Perbaiki sanitasi.'}, version=first['id']).status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.publication_status, 'NOT_DECIDED')
        second = self.candidate({'summary': 'Ringkasan kedua.'}, first['id'])
        self.assertEqual(self.post('cancel', {'reason': 'Periksa kembali.'}, version=second['id']).status_code, 200)
        self.prepare()
        stale = self.post('create', {'parent_id': first['id']})
        self.assertEqual(stale.status_code, 409, stale.content)
        third = self.post('create', {'parent_id': second['id']})
        self.assertEqual(third.status_code, 201, third.content)
        data = third.json()['data']['object']
        self.assertEqual(data['version_number'], 3)
        self.assertEqual(data['data']['summary'], 'Ringkasan kedua.')
        self.assertEqual(PublicationVersion.objects.filter(state='CANCELLED').count(), 2)

    def test_old_publication_stays_visible_during_replacement_approval_and_cancel(self):
        first = self.publish({'summary': 'Informasi publik semula.'})
        replacement = self.candidate({'summary': 'Kandidat belum boleh terbaca.'}, first['id'])
        self.assertEqual(self.public(f'{self.report.id}/').json()['data']['summary'], 'Informasi publik semula.')
        self.assertEqual(self.post('approve', version=replacement['id']).status_code, 200)
        self.assertEqual(self.public(f'{self.report.id}/').json()['data']['summary'], 'Informasi publik semula.')
        self.assertEqual(self.post('cancel', {'reason': 'Belum siap.'}, version=replacement['id']).status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(str(self.report.published_version_id), first['id'])
        self.assertEqual(self.report.publication_status, 'PUBLISHED')
        self.assertEqual(self.public().json()['count'], 1)

    def test_replacement_publish_switches_only_public_pointer_and_review_is_locked(self):
        first = self.publish({'summary': 'Versi publik pertama.'})
        original_card, original_review = self.report.official_card_version_id, self.report.latest_review_id
        self.prepare()
        self.report.refresh_from_db()
        response = self.client.post(f'/api/v1/workspace/reports/{self.report.id}/reviews/',
            {'outcome': 'VALID', 'reason': 'Tidak boleh review ulang.', 'expected_revision': self.report.revision},
            format='json', HTTP_IDEMPOTENCY_KEY=str(uuid4()))
        self.assertEqual(response.status_code, 422, response.content)
        created = self.post('create', {'parent_id': first['id'], 'data': {'summary': 'Versi publik kedua.'}})
        second = created.json()['data']['object']
        self.assertEqual(self.post('approve', version=second['id']).status_code, 200)
        self.assertEqual(self.post('publish', version=second['id']).status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.official_card_version_id, original_card)
        self.assertEqual(self.report.latest_review_id, original_review)
        self.assertEqual(self.public(f'{self.report.id}/').json()['data']['summary'], 'Versi publik kedua.')
        self.assertEqual(PublicationVersion.objects.filter(state='PUBLISHED').count(), 2)
        self.assertEqual(self.public().json()['count'], 1)
        self.assertEqual(self.post('cancel', {'reason': 'Tarik terbit.'}, version=second['id']).status_code, 422)

    def test_idempotent_replay_precedes_lifecycle_and_revision_but_not_current_permission(self):
        candidate = self.candidate()
        self.post('approve', version=candidate['id'])
        self.report.refresh_from_db(); revision = self.report.revision; key = uuid4()
        first = self.post('publish', version=candidate['id'], key=key, revision=revision)
        self.assertEqual(first.status_code, 200)
        self.report.workflow_status = 'CLOSED'; self.report.closed_at = timezone.now()
        self.report.closed_by = self.operator; self.report.closure_note = 'Ditutup setelah terbit.'
        self.report.revision += 1
        self.report.save(update_fields=['workflow_status', 'closed_at', 'closed_by', 'closure_note', 'revision'])
        replay = self.post('publish', version=candidate['id'], key=key, revision=revision)
        self.assertEqual(replay.status_code, 200, replay.content)
        self.assertEqual(replay['Idempotency-Replayed'], 'true')
        self.assertEqual(replay.json(), first.json())
        self.assertEqual(Notification.objects.filter(kind='REPORT_PUBLISHED').count(), 1)
        self.operator.user_permissions.clear()
        denied = self.post('publish', version=candidate['id'], key=key, revision=revision)
        self.assertEqual(denied.status_code, 403)

    def test_revision_conflict_and_approval_body_cannot_replace_content(self):
        candidate = self.candidate()
        self.report.refresh_from_db()
        self.assertEqual(self.post('approve', version=candidate['id'], revision=self.report.revision - 1).status_code, 409)
        self.assertEqual(self.post('approve', {'data': {'summary': 'Ganti diam-diam.'}}, version=candidate['id']).status_code, 400)
        self.assertEqual(PublicationVersion.objects.get(pk=candidate['id']).state, 'DRAFT')

    def test_candidate_audit_failure_rolls_back_version_revision_and_ledger(self):
        self.prepare()
        self.report.refresh_from_db()
        revision, key = self.report.revision, uuid4()
        with patch('reporting.publication_services.record_event', side_effect=RuntimeError('Audit unavailable')):
            response = self.post('create', {'parent_id': None}, key=key, revision=revision)
        self.assertEqual(response.status_code, 500, response.content)
        self.report.refresh_from_db()
        self.assertEqual(self.report.revision, revision)
        self.assertEqual(self.report.publication_status, 'PENDING_APPROVAL')
        self.assertIsNone(self.report.active_publication_candidate_id)
        self.assertFalse(PublicationVersion.objects.filter(report=self.report).exists())
        self.assertFalse(IdempotencyRecord.objects.filter(actor=self.operator, key=key).exists())
        self.assertFalse(AuditEvent.objects.filter(report=self.report, action='PUBLICATION_CANDIDATE_CREATED').exists())
        retry = self.post('create', {'parent_id': None}, key=key, revision=revision)
        self.assertEqual(retry.status_code, 201, retry.content)
        self.assertEqual(PublicationVersion.objects.filter(report=self.report).count(), 1)
        self.assertEqual(AuditEvent.objects.filter(report=self.report, action='PUBLICATION_CANDIDATE_CREATED').count(), 1)

    def test_notification_failure_rolls_back_publication_and_allows_exact_retry(self):
        candidate = self.candidate()
        self.assertEqual(self.post('approve', version=candidate['id']).status_code, 200)
        self.report.refresh_from_db()
        revision, key = self.report.revision, uuid4()
        with patch('reporting.publication_services.notify', side_effect=RuntimeError('Notification unavailable')):
            response = self.post('publish', version=candidate['id'], key=key, revision=revision)
        self.assertEqual(response.status_code, 500, response.content)
        self.report.refresh_from_db()
        version = PublicationVersion.objects.get(pk=candidate['id'])
        self.assertEqual(version.state, 'APPROVED')
        self.assertIsNone(version.published_at)
        self.assertIsNone(version.published_by_id)
        self.assertEqual(self.report.revision, revision)
        self.assertEqual(self.report.publication_status, 'APPROVED')
        self.assertEqual(str(self.report.active_publication_candidate_id), candidate['id'])
        self.assertIsNone(self.report.published_version_id)
        self.assertEqual(self.public().json()['count'], 0)
        self.assertFalse(IdempotencyRecord.objects.filter(actor=self.operator, key=key).exists())
        self.assertFalse(AuditEvent.objects.filter(report=self.report, action='REPORT_PUBLISHED').exists())
        self.assertFalse(Notification.objects.filter(report=self.report, kind='REPORT_PUBLISHED').exists())
        retry = self.post('publish', version=candidate['id'], key=key, revision=revision)
        self.assertEqual(retry.status_code, 200, retry.content)
        self.assertEqual(Notification.objects.filter(report=self.report, kind='REPORT_PUBLISHED').count(), 1)
        self.assertEqual(AuditEvent.objects.filter(report=self.report, action='REPORT_PUBLISHED').count(), 1)

    def test_published_projection_cannot_leak_unexpected_historical_json_keys(self):
        raw = {'event_type': 'FLOOD', 'summary': 'Informasi aman.', 'general_location': None, 'time_text': None,
               'occurred_at': None, 'general_impact': None, 'handling_update': None,
               'reporter_email': self.owner.email, 'raw_output': {'private': 'Jalan privat nomor 17'}}
        version = PublicationVersion(report=self.report, card_version=self.card, version_number=1,
            data=raw, state='PUBLISHED', sanitized_by=self.operator, approved_by=self.operator,
            approved_at=timezone.now(), published_by=self.operator, published_at=timezone.now())
        # Simulate malformed legacy storage without weakening model validation.
        PublicationVersion.objects.bulk_create([version])
        self.report.published_version = version; self.report.publication_status = 'PUBLISHED'
        self.report.save(update_fields=['published_version', 'publication_status'])
        for response in [self.public(), self.public(f'{self.report.id}/')]:
            self.assertEqual(response.status_code, 200)
            for hidden in [self.owner.email, 'reporter_email', 'raw_output', 'Jalan privat', str(version.id)]:
                self.assertNotIn(hidden, response.content.decode())
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/v1/reports/{self.report.id}/versions/PublicationVersion/{version.id}/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotIn('reporter_email', response.content.decode())

    def test_public_search_uses_only_allowed_fields_literal_matching_and_fixed_order(self):
        self.publish({'summary': 'BANJIR 50% di kawasan umum.', 'general_location': 'Natar',
                      'time_text': 'rahasia-waktu', 'handling_update': 'Evakuasi berlangsung.'})
        for query in ['banjir', 'NATAR', 'Evakuasi', '50%']:
            self.assertEqual(self.public('?q=' + query).json()['count'], 1)
        for query in ['rahasia-waktu', str(self.report.id), self.owner.email, '_']:
            self.assertEqual(self.public('?q=' + query).json()['count'], 0)
        self.assertEqual(self.public('?event_type=FIRE&q=banjir').json()['count'], 0)
        self.assertEqual(self.public('?event_type=FLOOD&general_location=Natar').json()['count'], 1)
        for query in ['?ordering=published_at', '?private=true', '?event_type=NON_EVENT', '?page_size=101', '?q=a&q=b']:
            self.assertEqual(self.public(query).status_code, 400, query)
        self.assertEqual(self.public('?page_size=1').json()['count'], 1)

    def test_anonymous_public_access_ignores_expired_authorization_but_private_candidates_stay_private(self):
        version = self.publish({'summary': 'Aman untuk publik.'})
        response = APIClient().get('/api/v1/public/reports/', HTTP_AUTHORIZATION='Bearer expired-and-invalid')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'no-store')
        candidate = self.candidate({'summary': 'Draf pengganti privat.'}, version['id'])
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/v1/reports/{self.report.id}/versions/PublicationVersion/{candidate["id"]}/')
        self.assertEqual(response.status_code, 404)

    def test_candidate_uses_official_corrected_card_instead_of_raw_nara(self):
        report, _, _, original, _ = source_chain(self.owner, official=False)
        corrected = IncidentCardVersion.objects.create(report=report, bundle=original.bundle, narrative=original.narrative,
            sena_result=original.sena_result, nara_result=original.nara_result, parent=original,
            version_number=2, source_kind='REPORTER_FIELD_REVISION',
            data={**original.data, 'location_text': 'Lokasi resmi hasil koreksi', 'impacts': ['Dampak resmi']},
            fusion_version=original.fusion_version, created_by=self.owner)
        HumanVerification.objects.create(report=report, card_version=corrected, reporter=self.owner, confirmed_at=timezone.now())
        report.current_card_version = report.official_card_version = corrected
        report.preparation_status = 'READY'; report.submitted_at = timezone.now(); report.workflow_status = 'IN_REVIEW'
        assignment = OperatorAssignment.objects.create(report=report, operator=self.operator, assigned_by=self.operator,
                                                       source='SELF_CLAIM', started_at=timezone.now())
        report.latest_review = OperatorReview.objects.create(report=report, card_version=corrected, assignment=assignment,
            operator=self.operator, outcome='VALID', reason='Koreksi sesuai sumber.', reviewed_at=timezone.now())
        report.validation_status = 'VALID'; report.save()
        self.report = report
        data = self.candidate()['data']
        self.assertEqual(data['general_location'], 'Lokasi resmi hasil koreksi')
        self.assertEqual(data['general_impact'], 'Dampak resmi')
        self.assertIsNone(corrected.nara_result.normalized_output['location_text'])


@skipUnless(connection.vendor == 'postgresql', 'Memerlukan lock dan transaksi PostgreSQL 16 asli.')
class PublicationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        call_command('bootstrap_silar', verbosity=0)
        self.owner = user('concurrent-owner@example.test')
        self.operator = user('concurrent-publisher@example.test', role='OPERATOR', perms=OPERATOR_PERMISSIONS)
        self.report, _ = reviewed_report(self.owner, self.operator)

    def concurrent(self, suffix, body, keys):
        barrier = Barrier(2)
        def request(key):
            close_old_connections()
            try:
                client = APIClient(); client.force_authenticate(user=self.operator)
                barrier.wait(timeout=10)
                response = client.post(f'/api/v1/reports/{self.report.id}/{suffix}', body,
                                       format='json', HTTP_IDEMPOTENCY_KEY=str(key))
                return response.status_code, response.get('Idempotency-Replayed')
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(request, keys))

    def test_concurrent_candidate_creation_commits_only_one_active_version(self):
        client = APIClient(); client.force_authenticate(user=self.operator)
        client.post(f'/api/v1/reports/{self.report.id}/publication-decision/',
                    {'decision': 'PREPARE', 'reason': 'Siapkan.', 'expected_revision': self.report.revision},
                    format='json', HTTP_IDEMPOTENCY_KEY=str(uuid4()))
        self.report.refresh_from_db()
        result = self.concurrent('publication-versions/', {'parent_id': None, 'expected_revision': self.report.revision},
                                 [uuid4(), uuid4()])
        self.assertEqual(sorted(status for status, _ in result), [201, 409])
        self.assertEqual(PublicationVersion.objects.filter(report=self.report).count(), 1)

    def test_concurrent_publish_replay_has_one_notification_and_one_audit(self):
        client = APIClient(); client.force_authenticate(user=self.operator)
        def post(suffix, body):
            self.report.refresh_from_db()
            return client.post(f'/api/v1/reports/{self.report.id}/{suffix}',
                {'expected_revision': self.report.revision, **body}, format='json', HTTP_IDEMPOTENCY_KEY=str(uuid4()))
        post('publication-decision/', {'decision': 'PREPARE', 'reason': 'Siapkan.'})
        response = post('publication-versions/', {'parent_id': None})
        version = response.json()['data']['object']['id']
        post(f'publication-versions/{version}/approve/', {})
        self.report.refresh_from_db(); key = uuid4()
        result = self.concurrent(f'publication-versions/{version}/publish/', {'expected_revision': self.report.revision}, [key, key])
        self.assertEqual([status for status, _ in result], [200, 200])
        self.assertEqual(sum(replayed == 'true' for _, replayed in result), 1)
        self.assertEqual(Notification.objects.filter(report=self.report, kind='REPORT_PUBLISHED').count(), 1)
        self.assertEqual(AuditEvent.objects.filter(report=self.report, action='REPORT_PUBLISHED').count(), 1)
