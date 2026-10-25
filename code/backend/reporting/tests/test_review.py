"""SLR12 API contracts; use PostgreSQL 16 for migration/locking acceptance."""
import uuid
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from common.testing import user
from core.models import AuditEvent, HumanVerification, IdempotencyRecord, IncidentCardVersion, NarrativeVersion, Notification, PublicationVersion, Report
from core.test_fixtures import source_chain


class ReporterReviewTests(TestCase):
    def setUp(self):
        self.owner = user()
        self.other = user(email='other@example.test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.report, self.bundle, self.run, self.card, self.evidence = source_chain(self.owner, uncertain=True)

    def post(self, suffix, data=None, key=None, report=None):
        report = report or self.report
        report.refresh_from_db()
        if data is None:
            data = {'card_version_id': str(report.current_card_version_id), 'expected_revision': report.revision}
        return self.client.post(f'/api/v1/reports/{report.id}/{suffix}/', data, format='json',
                                HTTP_IDEMPOTENCY_KEY=str(key or uuid.uuid4()))

    def revise(self, **patch_values):
        self.report.refresh_from_db()
        return self.post('cards/revisions', {'parent_id': str(self.report.current_card_version_id),
            'patch': patch_values or {'location_text': 'Jalan Melati'}, 'expected_revision': self.report.revision})

    def confirm(self):
        result = self.post('human-verifications')
        self.assertEqual(result.status_code, 201, result.data)
        return result

    def test_confirm_binds_version_without_submitting_or_clearing_uncertainty(self):
        response = self.confirm()
        self.report.refresh_from_db()
        self.assertEqual(response.data['data']['object']['card_version_id'], str(self.card.id))
        self.assertEqual(self.report.preparation_status, 'READY')
        self.assertIsNone(self.report.submitted_at)
        self.assertEqual(self.report.workflow_status, 'NOT_SUBMITTED')
        self.card.refresh_from_db()
        self.assertTrue(self.card.uncertain)

    def test_confirm_same_version_new_key_returns_existing_without_revision_or_audit_change(self):
        first = self.confirm()
        self.report.refresh_from_db()
        revision, audits = self.report.revision, AuditEvent.objects.count()
        second = self.post('human-verifications')
        self.assertEqual(second.status_code, 200, second.data)
        self.assertEqual(second.data['data']['object'], first.data['data']['object'])
        self.report.refresh_from_db()
        self.assertEqual(self.report.revision, revision)
        self.assertEqual(AuditEvent.objects.count(), audits)
        self.assertEqual(HumanVerification.objects.count(), 1)

    def test_card_correction_keeps_sources_raw_results_and_old_confirmation(self):
        self.confirm()
        response = self.revise(location_text='Jalan Melati', victims=[], occurred_at='2026-10-23T07:00:00+07:00')
        self.assertEqual(response.status_code, 201, response.data)
        newer = IncidentCardVersion.objects.get(pk=response.data['data']['object']['id'])
        self.assertEqual(newer.parent_id, self.card.id)
        for field in ['bundle_id', 'narrative_id', 'sena_result_id', 'nara_result_id', 'uncertain', 'uncertain_reasons', 'fusion_version']:
            self.assertEqual(getattr(newer, field), getattr(self.card, field))
        self.card.refresh_from_db()
        self.assertIsNone(self.card.data['location_text'])
        detail = self.client.get(f'/api/v1/reports/{self.report.id}/').data['data']
        self.assertIsNone(detail['verification'])
        self.assertEqual(detail['report']['preparation_status'], 'AWAITING_CONFIRMATION')
        self.assertEqual(HumanVerification.objects.count(), 1)

    def test_old_confirmation_cannot_submit_corrected_version(self):
        self.confirm()
        self.assertEqual(self.revise().status_code, 201)
        result = self.post('submit')
        self.assertEqual(result.status_code, 422, result.data)
        self.assertEqual(result.data['error']['code'], 'VERIFICATION_REQUIRED')
        self.report.refresh_from_db()
        self.assertIsNone(self.report.submitted_at)

    def test_submit_requires_confirmation_but_missing_incident_fields_do_not_block(self):
        self.assertEqual(self.post('submit').status_code, 422)
        self.confirm()
        result = self.post('submit')
        self.assertEqual(result.status_code, 200, result.data)
        self.report.refresh_from_db()
        self.assertEqual(self.report.official_card_version_id, self.card.id)
        self.assertEqual(self.report.workflow_status, 'SUBMITTED')
        self.assertEqual(Notification.objects.get().kind, 'REPORT_SUBMITTED')

    def test_submitted_report_enters_existing_queue_scope_without_private_summary_fields(self):
        self.confirm()
        self.post('submit')
        operator = user(email='operator@example.test', role='OPERATOR', perms=['view_queue'])
        self.client.force_authenticate(user=operator)
        result = self.client.get('/api/v1/reports/?scope=queue')
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['results'][0]['id'], str(self.report.id))
        self.assertNotIn('data', result.data['results'][0])
        self.assertNotIn('owner_id', result.data['results'][0])

    def test_submit_replay_uses_original_snapshot_and_never_duplicates_notification(self):
        self.confirm()
        self.report.refresh_from_db()
        body = {'card_version_id': str(self.card.id), 'expected_revision': self.report.revision}
        key = uuid.uuid4()
        first = self.post('submit', body, key)
        second = self.post('submit', body, key)
        self.assertEqual(second.status_code, 200, second.data)
        self.assertEqual(second.data, first.data)
        self.assertEqual(second['Idempotency-Replayed'], 'true')
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action='REPORT_SUBMITTED').count(), 1)
        self.assertEqual(self.post('submit').status_code, 422)

    def test_submitted_owner_cannot_correct_or_confirm_again(self):
        self.confirm()
        self.post('submit')
        self.assertEqual(self.revise().status_code, 422)
        self.assertEqual(self.post('human-verifications').status_code, 422)
        self.report.refresh_from_db()
        self.assertEqual(self.post('narratives/revisions', {'parent_id': str(self.card.narrative_id),
            'text': 'Revisi sesudah pengiriman.', 'expected_revision': self.report.revision}).status_code, 422)

    def test_narrative_revision_invalidates_card_increments_source_and_preserves_original(self):
        self.confirm()
        self.report.refresh_from_db()
        old_revision, old_input = self.report.revision, self.report.input_revision
        response = self.post('narratives/revisions', {'parent_id': str(self.card.narrative_id),
            'text': '  Air menggenangi Jalan Melati.  ', 'expected_revision': old_revision})
        self.assertEqual(response.status_code, 201, response.data)
        self.report.refresh_from_db()
        self.assertEqual(self.report.revision, old_revision + 1)
        self.assertEqual(self.report.input_revision, old_input + 1)
        self.assertIsNone(self.report.current_card_version_id)
        self.assertEqual(self.report.preparation_status, 'DRAFT')
        newer = self.report.active_narrative
        self.assertEqual(newer.parent_id, self.card.narrative_id)
        self.assertEqual(newer.origin, 'REPORTER_REVISION')
        self.assertIsNone(newer.producer_run_id)
        self.assertEqual(newer.text, '  Air menggenangi Jalan Melati.  ')
        self.assertEqual(IncidentCardVersion.objects.count(), 1)
        self.assertEqual(self.report.analysis_runs.count(), 1)

    def test_narrative_can_change_while_unknown_run_remains_reserved(self):
        self.run.status = 'UNKNOWN'
        self.run.finished_at = None
        self.run.save()
        result = self.post('narratives/revisions', {'parent_id': str(self.card.narrative_id),
            'text': 'Sumber direvisi sambil menunggu pemulihan.', 'expected_revision': self.report.revision})
        self.assertEqual(result.status_code, 201, result.data)
        self.run.refresh_from_db()
        self.assertEqual(self.run.status, 'UNKNOWN')
        self.assertEqual(self.run.capacity_slot, 1)

    def test_new_bundle_rejects_old_card_confirmation(self):
        self.confirm()
        self.report.refresh_from_db()
        result = self.post('bundles', {'evidence_ids': [str(self.evidence.id)], 'expected_revision': self.report.revision})
        self.assertEqual(result.status_code, 201, result.data)
        response = self.post('human-verifications', {'card_version_id': str(self.card.id),
            'expected_revision': result.data['data']['report']['revision']})
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(HumanVerification.objects.count(), 1)

    def test_source_or_incomplete_run_cannot_be_confirmed(self):
        self.run.status = 'FAILED'
        self.run.error_code = 'AI_MODEL_FAILED'
        self.run.save()
        response = self.post('human-verifications')
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(response.data['error']['code'], 'SOURCE_CONFLICT')
        self.assertFalse(HumanVerification.objects.exists())

    def test_failed_preparation_cannot_confirm_a_leftover_card(self):
        self.report.preparation_status = 'FAILED'
        self.report.save(update_fields=['preparation_status'])
        result = self.post('human-verifications')
        self.assertEqual(result.status_code, 409, result.data)
        self.assertEqual(result.data['error']['code'], 'SOURCE_CONFLICT')
        self.assertFalse(HumanVerification.objects.exists())

    def test_non_event_stays_blocked_after_field_correction_and_cannot_confirm(self):
        report, _, _, card, _ = source_chain(self.owner, category='NON_EVENT')
        response = self.post('cards/revisions', {'parent_id': str(card.id), 'patch': {'location_text': 'Lokasi sumber'},
            'expected_revision': report.revision}, report=report)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['data']['report']['preparation_status'], 'BLOCKED')
        for endpoint in ['human-verifications', 'submit']:
            result = self.post(endpoint, report=report)
            self.assertEqual(result.status_code, 422, result.data)
            self.assertEqual(result.data['error']['code'], 'NON_EVENT')

    def test_patch_rejects_category_unknown_null_list_and_naive_time(self):
        for patch_values in [{'event_type': 'FIRE'}, {'private_note': 'secret'}, {}, {'victims': None},
                             {'victims': [12]}, {'location_text': 15}, {'occurred_at': '2026-10-23T12:00:00'},
                             {'occurred_at': 'pagi ini'}, {'impacts': ['x' * 501]}]:
            with self.subTest(patch=patch_values):
                response = self.post('cards/revisions', {'parent_id': str(self.card.id), 'patch': patch_values,
                    'expected_revision': self.report.revision})
                self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(IncidentCardVersion.objects.count(), 1)

    def test_stale_revision_and_stale_parent_do_not_create_versions(self):
        revision = self.report.revision
        self.assertEqual(self.revise().status_code, 201)
        old_revision = self.post('cards/revisions', {'parent_id': str(self.card.id),
            'patch': {'time_text': 'pagi'}, 'expected_revision': revision})
        self.assertEqual(old_revision.data['error']['code'], 'REVISION_CONFLICT')
        self.report.refresh_from_db()
        old_parent = self.post('cards/revisions', {'parent_id': str(self.card.id),
            'patch': {'time_text': 'pagi'}, 'expected_revision': self.report.revision})
        self.assertEqual(old_parent.data['error']['code'], 'VERSION_CONFLICT')
        self.assertEqual(IncidentCardVersion.objects.count(), 2)

    def test_correction_replay_precedes_stale_revision_and_parent_checks(self):
        body = {'parent_id': str(self.card.id), 'patch': {'location_text': 'Jalan Melati'}, 'expected_revision': self.report.revision}
        key = uuid.uuid4()
        first = self.post('cards/revisions', body, key)
        second = self.post('cards/revisions', body, key)
        self.assertEqual(second.data, first.data)
        self.assertEqual(second['Idempotency-Replayed'], 'true')
        changed = self.post('cards/revisions', dict(body, patch={'location_text': 'Berbeda'}), key)
        self.assertEqual(changed.data['error']['code'], 'IDEMPOTENCY_MISMATCH')
        self.assertEqual(IncidentCardVersion.objects.count(), 2)

    def test_other_owner_missing_report_and_revoked_actor_do_not_replay(self):
        first = self.confirm()
        record = IdempotencyRecord.objects.get(result_id=uuid.UUID(first.data['data']['object']['id']))
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.post('human-verifications').status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/reports/{self.report.id}/versions/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/reports/{self.report.id}/history/').status_code, 404)
        self.client.force_authenticate(user=self.owner)
        self.owner.role = 'OPERATOR'
        self.owner.save(update_fields=['role'])
        response = self.post('human-verifications', {'card_version_id': str(self.card.id), 'expected_revision': 1}, record.key)
        self.assertEqual(response.status_code, 403)

    def test_missing_report_and_missing_idempotency_key_use_safe_errors(self):
        response = self.client.post(f'/api/v1/reports/{uuid.uuid4()}/submit/', {}, format='json')
        self.assertEqual(response.status_code, 404)
        response = self.client.post(f'/api/v1/reports/{self.report.id}/human-verifications/',
            {'card_version_id': str(self.card.id), 'expected_revision': self.report.revision}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_card_audit_failure_rolls_back_version_ledger_and_report(self):
        ledgers = IdempotencyRecord.objects.count()
        with patch('reporting.review_services.record_event', side_effect=RuntimeError('rollback fixture')):
            response = self.revise()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(IncidentCardVersion.objects.count(), 1)
        self.assertEqual(IdempotencyRecord.objects.count(), ledgers)
        self.report.refresh_from_db()
        self.assertEqual(self.report.revision, 1)

    def test_submit_notification_failure_rolls_back_official_pointer_and_audit(self):
        self.confirm()
        ledgers, audits = IdempotencyRecord.objects.count(), AuditEvent.objects.count()
        with patch('reporting.review_services.notify', side_effect=RuntimeError('rollback fixture')):
            result = self.post('submit')
        self.assertEqual(result.status_code, 500)
        self.report.refresh_from_db()
        self.assertIsNone(self.report.submitted_at)
        self.assertIsNone(self.report.official_card_version_id)
        self.assertEqual(self.report.workflow_status, 'NOT_SUBMITTED')
        self.assertEqual(IdempotencyRecord.objects.count(), ledgers)
        self.assertEqual(AuditEvent.objects.count(), audits)

    def test_version_list_is_paginated_metadata_and_old_detail_is_immutable_source(self):
        self.revise(location_text='Jalan Melati')
        url = f'/api/v1/reports/{self.report.id}/versions/'
        result = self.client.get(url+'?kind=IncidentCardVersion&page_size=1')
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['count'], 2)
        self.assertEqual(result.data['results'][0]['id'], str(self.card.id))
        self.assertNotIn('data', result.data['results'][0])
        self.assertNotIn('text', result.data['results'][0])
        old = self.client.get(url+f'IncidentCardVersion/{self.card.id}/')
        self.assertIsNone(old.data['data']['version']['data']['location_text'])
        self.assertEqual(old['Cache-Control'], 'no-store')
        self.assertEqual(self.client.get(url+'?q=private').status_code, 400)
        self.assertEqual(self.client.get(url+'?kind=Unknown').status_code, 400)
        foreign, _, _, foreign_card, _ = source_chain(self.other)
        self.assertEqual(self.client.get(url+f'IncidentCardVersion/{foreign_card.id}/').status_code, 404)

    def test_official_flags_and_history_exclude_internal_audit_fields(self):
        self.confirm()
        self.post('submit')
        url = f'/api/v1/reports/{self.report.id}/'
        versions = self.client.get(url+'versions/').data['results']
        self.assertEqual(len(versions), 3)
        self.assertTrue(all(row['official'] for row in versions))
        AuditEvent.objects.create(report=self.report, actor=self.owner, actor_role='OPERATOR', action='REVIEW_RECORDED',
            object_type='OperatorReview', after={'reason': 'PRIVATE_OPERATOR_SENTINEL', 'workflow_status': 'IN_REVIEW'})
        history = self.client.get(url+'history/?page_size=100')
        self.assertNotIn('PRIVATE_OPERATOR_SENTINEL', str(history.data))
        self.assertTrue(all(set(row) == {'id', 'action', 'actor_role', 'created_at', 'card_version_id', 'states'} for row in history.data['results']))
        self.assertEqual(self.client.get(url+'history/?q=private').status_code, 400)

    def test_reporter_and_monitor_receive_only_published_public_version_projection(self):
        self.confirm()
        self.post('submit')
        self.report.refresh_from_db()
        operator = user(email='operator@example.test', role='OPERATOR')
        public = {'event_type': 'FLOOD', 'summary': 'Genangan jalan umum.', 'general_location': None,
            'time_text': None, 'occurred_at': None, 'general_impact': None, 'handling_update': None}
        candidate = PublicationVersion.objects.create(report=self.report, card_version=self.card,
            version_number=1, data=public, sanitized_by=operator)
        url = f'/api/v1/reports/{self.report.id}/versions/'
        self.assertEqual(self.client.get(url+f'PublicationVersion/{candidate.id}/').status_code, 404)
        self.assertEqual(self.client.get(url+'?kind=PublicationVersion').data['count'], 0)
        published = PublicationVersion.objects.create(report=self.report, card_version=self.card,
            version_number=2, parent=candidate, data=public, state='PUBLISHED', sanitized_by=operator,
            approved_by=operator, approved_at=timezone.now(), published_by=operator, published_at=timezone.now())
        result = self.client.get(url+f'PublicationVersion/{published.id}/')
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['data']['version']['id'], str(self.report.id))
        for field in ['card_version_id', 'sanitized_by', 'data', 'parent_id']:
            self.assertNotIn(field, result.data['data']['version'])
        monitor = user(email='monitor@example.test', role='ADMIN', perms=['monitor_report'])
        self.client.force_authenticate(user=monitor)
        result = self.client.get(url)
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(self.client.get(url+f'IncidentCardVersion/{self.card.id}/').status_code, 404)


class NotificationTests(TestCase):
    def setUp(self):
        self.owner = user()
        self.other = user(email='other@example.test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.report = Report.objects.create(owner=self.owner)
        self.mine = Notification.objects.create(recipient=self.owner, report=self.report,
            kind='REPORT_SUBMITTED', message='Laporan sudah dikirim.')
        self.theirs = Notification.objects.create(recipient=self.other, kind='REPORT_ASSIGNED', message='Tugas baru.')

    def test_list_is_recipient_only_paginated_no_recipient_identity(self):
        result = self.client.get('/api/v1/notifications/?page_size=1&unread=true')
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['id'], str(self.mine.id))
        self.assertNotIn('recipient_id', result.data['results'][0])
        self.assertEqual(result['Cache-Control'], 'no-store')

    def test_repeat_read_preserves_first_timestamp_and_report_revision(self):
        url = f'/api/v1/notifications/{self.mine.id}/read/'
        first = self.client.patch(url, {}, format='json')
        second = self.client.patch(url, {}, format='json')
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data, second.data)
        self.report.refresh_from_db()
        self.assertEqual(self.report.revision, 1)
        self.assertEqual(self.client.get('/api/v1/notifications/?unread=true').data['count'], 0)
        self.assertEqual(self.client.get('/api/v1/notifications/?unread=false').data['count'], 1)

    def test_foreign_read_unknown_body_and_invalid_query_rejected(self):
        self.assertEqual(self.client.patch(f'/api/v1/notifications/{self.theirs.id}/read/', {}, format='json').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/v1/notifications/{self.mine.id}/read/', {'read_at': 'now'}, format='json').status_code, 400)
        for query in ['unread=yes', 'recipient_id='+str(self.other.id), 'page_size=101']:
            self.assertEqual(self.client.get('/api/v1/notifications/?'+query).status_code, 400)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/v1/notifications/').status_code, 401)
