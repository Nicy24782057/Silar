import uuid
from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient
from common.testing import user
from core.permissions import OPERATOR_PERMISSIONS
from core.test_fixtures import source_chain
from reporting import workspace_services as ops

class ShortcutFiltersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_silar',verbosity=0)
        cls.owner=user('ui02-owner@example.test')
        cls.andi=user('ui02-andi@example.test',role='OPERATOR',perms=OPERATOR_PERMISSIONS)
        cls.rina=user('ui02-rina@example.test',role='OPERATOR',perms=OPERATOR_PERMISSIONS)
        cls.ids={}
        for key,actor,outcome,pending,closed in [('review',cls.andi,None,0,False),('pending',cls.andi,'VALID',2,False),('reviewed',cls.andi,'INCONCLUSIVE',0,False),('closed',cls.andi,'INVALID',0,True),('other',cls.rina,None,0,False)]:
            report,*_=source_chain(cls.owner,official=True);cls.ids[key]=str(report.id)
            def write(fn,body):
                report.refresh_from_db()
                return fn(actor,report.id,uuid.uuid4(),{'expected_revision':report.revision,**body})
            write(ops.claim,{})
            if outcome:write(ops.review,{'outcome':outcome,'reason':'Bukti resmi sudah diperiksa.'})
            for i in range(pending):write(ops.followup,{'description':'Pemeriksaan tahap '+str(i+1)})
            if closed:write(ops.close,{'closure_note':'Penanganan sudah selesai.'})

    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(user=self.andi)

    def test_filters_match_counts_and_keep_assignment_scope_without_duplicates(self):
        counts=self.client.get('/api/v1/workspace/dashboard/').json()['data']['counts']
        for query,key,ids in [('active=true','assigned',['review','pending','reviewed']),('active=true&validation_status=NOT_REVIEWED','review_pending',['review']),('active=true&followup_status=PENDING','followup_pending',['pending'])]:
            with self.subTest(query=query):
                r=self.client.get('/api/v1/workspace/reports/?scope=assigned&'+query)
                self.assertEqual(r.status_code,200,r.content)
                self.assertEqual(r.json()['count'],counts[key])
                self.assertEqual({x['id']for x in r.json()['results']},{self.ids[x]for x in ids})
        self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=assigned&active=false').json()['count'],1)

    def test_invalid_values_are_rejected_and_filters_do_not_grant_reporter_access(self):
        for query in ['active=all','validation_status=UNKNOWN','followup_status=DRAFT']:
            with self.subTest(query=query):self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=assigned&'+query).status_code,400)
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=assigned&active=true&validation_status=NOT_REVIEWED').status_code,403)
