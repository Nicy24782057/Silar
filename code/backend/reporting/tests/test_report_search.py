"""Reporter keyword/ID search must stay private, version-correct and read-only."""
import hashlib

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from common.testing import user
from core.models import AnalysisRun, AuditEvent, EvidenceBundle, EvidenceBundleItem, EvidenceItem, IdempotencyRecord, NarrativeVersion, Report
from core.test_fixtures import source_chain


class ReporterSearchTests(TestCase):
    def setUp(self):
        self.owner = user()
        self.other = user(email='search-other@example.test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def text(self, report, text):
        return EvidenceItem.objects.create(report=report, type='TEXT', text_content=text, byte_size=len(text.encode()),
                                          sha256=hashlib.sha256(text.encode()).hexdigest(), uploaded_by=report.owner)

    def get(self, q='', **filters):
        return self.client.get('/api/v1/reports/', {'scope': 'owned', 'q': q, **filters})

    def test_draft_text_search_is_case_insensitive_and_matches_all_words(self):
        report = Report.objects.create(owner=self.owner)
        self.text(report, 'Banjir di Jalan Melati dekat pasar.')
        response = self.get('  MELATI banjir  ')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(report.id))
        self.assertEqual(self.get('Melati kebakaran').data['count'], 0)

    def test_id_short_full_hyphenated_and_hash_forms(self):
        report = Report.objects.create(owner=self.owner)
        for term in (str(report.id), report.id.hex, str(report.id)[:8], '#' + str(report.id)[:8]):
            with self.subTest(term=term):
                response = self.get(term)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data['results'][0]['id'], str(report.id))

    def test_foreign_reports_never_appear_by_text_or_id(self):
        foreign = source_chain(self.other)[0]
        self.text(foreign, 'Penanda pribadi Melati')
        for query in ('Air', 'Melati', str(foreign.id), foreign.id.hex[:8]):
            self.assertEqual(self.get(query).data['count'], 0)

    def test_soft_deleted_draft_is_excluded(self):
        report = Report.objects.create(owner=self.owner, deleted_at=timezone.now(), deleted_by=self.owner)
        self.text(report, 'Melati')
        self.assertEqual(self.get('Melati').data['count'], 0)
        self.assertEqual(self.get(str(report.id)).data['count'], 0)

    def test_active_bundle_does_not_match_deselected_sources_or_old_narratives(self):
        report, _, _, _, _ = source_chain(self.owner)
        selected = self.text(report, 'Laporan terbaru Melati')
        bundle = EvidenceBundle.objects.create(report=report, version_number=2, source_digest='b' * 64, created_by=self.owner)
        EvidenceBundleItem.objects.create(bundle=bundle, evidence=selected, position=1)
        report.active_bundle = bundle
        report.active_narrative = None
        report.current_card_version = None
        report.preparation_status = 'DRAFT'
        report.save()
        self.assertEqual(self.get('Air').data['count'], 0)
        self.assertEqual(self.get('Melati').data['count'], 1)

    def test_current_narrative_is_searchable(self):
        report, bundle, *_ = source_chain(self.owner)
        narrative = NarrativeVersion.objects.create(report=report, bundle=bundle, version_number=2,
            text='Rumah terbakar di Melati.', origin='REPORTER_REVISION', created_by=self.owner)
        report.active_narrative = narrative
        report.save()
        self.assertEqual(self.get('Melati terbakar').data['count'], 1)

    def test_submitted_report_uses_official_narrative_and_bundle(self):
        report, bundle, *_ = source_chain(self.owner, official=True)
        narrative = NarrativeVersion.objects.create(report=report, bundle=bundle, version_number=2,
            text='Istilah sesudah versi resmi', origin='REPORTER_REVISION', created_by=self.owner)
        self.text(report, 'Bukti di luar versi resmi')
        self.assertEqual(self.get('Air jalan').data['count'], 1)
        self.assertEqual(self.get('sesudah').data['count'], 0)
        self.assertEqual(self.get('luar').data['count'], 0)

    def test_search_filters_before_count_and_pagination_without_duplicates(self):
        for _ in range(7):
            report = Report.objects.create(owner=self.owner)
            self.text(report, 'Melati');self.text(report, 'Melati kedua')
        source_chain(self.other)
        first = self.get('Melati', page_size=5)
        self.assertEqual(first.data['count'], 7)
        self.assertEqual(len(first.data['results']), 5)
        self.assertIn('q=Melati', first.data['next'])
        second = self.get('Melati', page_size=5, page=2)
        self.assertEqual(second.data['count'], 7)
        self.assertEqual(len(second.data['results']), 2)
        self.assertFalse({x['id'] for x in first.data['results']} & {x['id'] for x in second.data['results']})

    def test_category_and_workflow_filters_combine_with_keywords(self):
        source_chain(self.owner, official=True, category='FLOOD')
        source_chain(self.owner, category='FIRE')
        response = self.get('Air', event_type='FLOOD', workflow_status='SUBMITTED')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['event_type'], 'FLOOD')

    def test_invalid_search_is_rejected_and_blank_search_stays_unfiltered(self):
        Report.objects.create(owner=self.owner)
        self.assertEqual(self.get('   ').data['count'], 1)
        for value in ('x' * 101, 'satu ' * 9, 'bad\x00query'):
            response = self.get(value)
            self.assertEqual(response.status_code, 400, response.data)
            self.assertEqual(response.data['error']['code'], 'INVALID_PAYLOAD')

    def test_search_does_not_mutate_reports_or_start_ai(self):
        report = source_chain(self.owner)[0]
        before = (AnalysisRun.objects.count(), AuditEvent.objects.count(), IdempotencyRecord.objects.count(), report.revision)
        for _ in range(2):self.assertEqual(self.get('Air').status_code, 200)
        report.refresh_from_db()
        self.assertEqual(before, (AnalysisRun.objects.count(), AuditEvent.objects.count(), IdempotencyRecord.objects.count(), report.revision))
