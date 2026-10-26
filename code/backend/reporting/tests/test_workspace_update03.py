import uuid
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient
from common.testing import user
from core.permissions import OPERATOR_PERMISSIONS
from core.test_fixtures import source_chain
from reporting import workspace_services as ops

class AdminShortcutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_silar',verbosity=0)
        cls.owner=user('ui03-owner@example.test')
        cls.andi=user('ui03-andi@example.test',role='OPERATOR',perms=OPERATOR_PERMISSIONS)
        cls.admin=user('ui03-admin@example.test',role='ADMIN',perms=['monitor_report','assign_report','manage_operator'])
        cls.inactive=user('ui03-inactive@example.test',role='OPERATOR',active=False)
        cls.pending=user('ui03-pending@example.test',role='OPERATOR',active=False,verified=False)
        cls.reports={}
        for key in ['unassigned','ended','assigned','closed','draft']:
            report,*_=source_chain(cls.owner,official=key!='draft');cls.reports[key]=report
            def write(fn,body):
                report.refresh_from_db();return fn(cls.andi,report.id,uuid.uuid4(),{'expected_revision':report.revision,**body})
            if key in ['ended','assigned','closed']:write(ops.claim,{})
            if key=='ended':
                item=report.assignments.get(ended_at__isnull=True);item.ended_at=timezone.now();item.save(update_fields=['ended_at'])
            if key=='closed':
                write(ops.review,{'outcome':'INVALID','reason':'Bukti tidak sesuai kejadian.'})
                write(ops.close,{'closure_note':'Penanganan telah selesai.'})

    def setUp(self):self.client=APIClient();self.client.force_authenticate(user=self.admin)

    def test_admin_lists_match_all_four_dashboard_counts(self):
        counts=self.client.get('/api/v1/workspace/dashboard/').json()['data']['counts']
        for query,key,names in [('scope=monitor','official',['unassigned','ended','assigned','closed']),('scope=assignment&active=true&unassigned=true','unassigned',['unassigned','ended']),('scope=monitor&workflow_status=CLOSED','closed',['closed'])]:
            with self.subTest(query=query):
                r=self.client.get('/api/v1/workspace/reports/?'+query);self.assertEqual(r.status_code,200,r.content)
                self.assertEqual(r.json()['count'],counts[key])
                self.assertEqual({x['id']for x in r.json()['results']},{str(self.reports[x].id)for x in names})
                self.assertNotIn(self.owner.email,r.content.decode())
        users=self.client.get('/api/v1/admin/operators/?page_size=100').json()['results']
        active=[x for x in users if x['is_active']and x['email_verified_at']]
        self.assertEqual(len(active),counts['operators']);self.assertEqual(len(active),1)

    def test_zero_unassigned_reports_returns_a_valid_empty_list_after_assignment(self):
        for key in ['unassigned','ended']:
            report=self.reports[key];report.refresh_from_db()
            ops.assign(self.admin,report.id,uuid.uuid4(),{'expected_revision':report.revision,'operator_id':self.andi.id,'reason':'Penetapan penanggung jawab.'})
        counts=self.client.get('/api/v1/workspace/dashboard/').json()['data']['counts']
        r=self.client.get('/api/v1/workspace/reports/?scope=assignment&active=true&unassigned=true')
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['results'],[])
        self.assertEqual(r.json()['count'],0);self.assertEqual(counts['unassigned'],0)

    def test_unassigned_filter_is_validated_and_cannot_grant_admin_scope(self):
        self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=monitor&unassigned=all').status_code,400)
        for person in [self.owner,self.andi]:
            self.client.force_authenticate(user=person)
            self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=assignment&unassigned=true').status_code,403)
        monitor=user('ui03-monitor@example.test',role='ADMIN',perms=['monitor_report']);self.client.force_authenticate(user=monitor)
        self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=assignment&unassigned=true').status_code,403)
        self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=monitor&active=true&unassigned=true').json()['count'],2)
