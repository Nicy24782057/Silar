"""Fixed Operator capabilities, eligibility and read-only account metadata."""
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from accounts import services
from accounts.models import Role
from common.testing import user
from core.models import AuditEvent
from core.permissions import (ADMIN_PERMISSIONS, OPERATOR_PERMISSIONS,
                              effective_permissions, operator_permission_ids,
                              permission_queryset)


class OperatorRoleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_silar', verbosity=0)
        cls.admin = user('role-admin@example.test', role=Role.ADMIN,
                         perms=['manage_operator', 'assign_report', 'view_audit'])
        cls.operator = user('role-operator@example.test', role=Role.OPERATOR)

    def setUp(self):
        self.client = APIClient()

    def bearer(self, person):
        access, _ = services.issue_tokens(person)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access)

    def test_existing_operator_without_grants_has_complete_role_in_me_and_queue(self):
        self.assertFalse(self.operator.user_permissions.exists())
        self.assertFalse(self.operator.groups.exists())
        self.bearer(self.operator)
        response = self.client.get('/api/v1/me/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(set(response.json()['data']['effective_permissions']), set(OPERATOR_PERMISSIONS))
        self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=queue').status_code, 200)

    def test_partial_legacy_grants_do_not_limit_role_or_allow_admin_privileges(self):
        self.operator.user_permissions.set(permission_queryset().filter(
            codename__in=['view_queue', 'review_report', 'manage_operator']))
        self.assertEqual(effective_permissions(self.operator), set(OPERATOR_PERMISSIONS))
        self.bearer(self.operator)
        self.assertEqual(self.client.get('/api/v1/admin/operators/').status_code, 403)
        self.assertEqual(self.client.get('/api/v1/workspace/audit/').status_code, 403)

    def test_group_grants_do_not_add_admin_privileges_to_operator(self):
        group = Group.objects.create(name='Legacy mixed role grants')
        group.permissions.set(permission_queryset().filter(codename__in=ADMIN_PERMISSIONS))
        self.operator.groups.add(group)
        self.operator.is_superuser = True
        self.operator.save(update_fields=['is_superuser'])
        self.assertEqual(effective_permissions(self.operator), set(OPERATOR_PERMISSIONS))

    def test_current_account_status_is_checked_on_existing_token(self):
        self.bearer(self.operator)
        self.assertEqual(self.client.get('/api/v1/me/').status_code, 200)
        for change in ({'is_active': False}, {'is_active': True, 'email_verified_at': None}):
            with self.subTest(change=change):
                for name, value in change.items():
                    setattr(self.operator, name, value)
                self.operator.save(update_fields=list(change))
                self.assertEqual(effective_permissions(self.operator), set())
                self.assertEqual(self.client.get('/api/v1/me/').status_code, 401)
                self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=queue').status_code, 401)

    def test_admin_does_not_inherit_operator_package(self):
        self.assertEqual(effective_permissions(self.admin),
                         {'manage_operator', 'assign_report', 'view_audit'})
        self.bearer(self.admin)
        self.assertEqual(self.client.get('/api/v1/workspace/reports/?scope=queue').status_code, 403)

    def test_assignment_targets_include_operator_without_legacy_grants(self):
        self.bearer(self.admin)
        response = self.client.get('/api/v1/workspace/assignment-targets/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual([row['id'] for row in response.json()['results']], [str(self.operator.id)])

    def test_account_permission_ids_are_fixed_metadata_even_before_activation(self):
        pending = user('pending-role@example.test', role=Role.OPERATOR, active=False, verified=False)
        disabled = user('disabled-role@example.test', role=Role.OPERATOR, active=False,
                        perms=['review_report'])
        self.bearer(self.admin)
        for person in (self.operator, pending, disabled):
            with self.subTest(person=person.email):
                response = self.client.get(f'/api/v1/admin/operators/{person.id}/')
                self.assertEqual(response.status_code, 200, response.content)
                data = response.json()['data']
                self.assertEqual(data['permission_ids'], operator_permission_ids())
                self.assertEqual(set(data['effective_permissions']),
                                 set(OPERATOR_PERMISSIONS) if person == self.operator else set())

    def test_patch_cannot_change_permissions_or_apply_accompanying_changes(self):
        self.bearer(self.admin)
        for ids in ([], operator_permission_ids(), [permission_queryset().get(codename='manage_operator').id]):
            with self.subTest(ids=ids):
                response = self.client.patch(f'/api/v1/admin/operators/{self.operator.id}/',
                    {'permission_ids': ids, 'full_name': 'Tidak boleh berubah',
                     'is_active': False, 'reason': 'Permintaan lama.'}, format='json')
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn('permission_ids', response.json()['error']['fields'])
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.full_name, 'Penguji SILAR')
        self.assertTrue(self.operator.is_active)
        self.assertFalse(AuditEvent.objects.filter(action='OPERATOR_UPDATED', object_id=self.operator.id).exists())

    def test_admin_disable_and_reactivate_preserves_complete_operator_role(self):
        access, _ = services.issue_tokens(self.operator)
        self.bearer(self.admin)
        response = self.client.patch(f'/api/v1/admin/operators/{self.operator.id}/',
            {'is_active': False, 'reason': 'Petugas sementara tidak bertugas.'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['data']['effective_permissions'], [])
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access)
        self.assertEqual(self.client.get('/api/v1/me/').status_code, 401)
        self.bearer(self.admin)
        response = self.client.patch(f'/api/v1/admin/operators/{self.operator.id}/',
            {'is_active': True, 'reason': 'Petugas kembali bertugas.'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(set(response.json()['data']['effective_permissions']), set(OPERATOR_PERMISSIONS))
        self.assertEqual(AuditEvent.objects.filter(action='OPERATOR_UPDATED', object_id=self.operator.id).count(), 2)
