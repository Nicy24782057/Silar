import uuid
import tempfile,os
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import TestCase,override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from common.testing import user,email_challenge,PASSWORD,NEW_PASSWORD
from core.models import AuditEvent
from core.permissions import permission_queryset,OPERATOR_PERMISSIONS
from .models import User,Role,EmailOTP,OTPPurpose
from . import services

class AccountAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):call_command('bootstrap_silar',verbosity=0)

    def setUp(self):
        self.client=APIClient(enforce_csrf_checks=True)
        csrf=self.client.get('/api/v1/auth/csrf/').json()['data']['csrf_token']
        self.client.credentials(HTTP_X_CSRFTOKEN=csrf)

    def post(self,path,data):return self.client.post('/api/v1/'+path,data,format='json')
    def register(self,email='baru@example.test',**extra):
        return self.post('auth/register/',dict(full_name='Pelapor Baru',email=email,
            password=PASSWORD,password_confirm=PASSWORD,**extra))
    def bearer(self,obj):
        access,_=services.issue_tokens(obj)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+access)
        return access
    def sign_in(self,obj):
        response=self.post('auth/login/',{'email':obj.email,'password':PASSWORD})
        self.assertEqual(response.status_code,200,response.content)
        return response

    def test_all_auth_posts_require_csrf(self):
        client=APIClient(enforce_csrf_checks=True)
        for endpoint in ['register','otp/request','otp/verify','operators/activate','password/reset','login','refresh','logout']:
            with self.subTest(endpoint=endpoint):
                response=client.post(f'/api/v1/auth/{endpoint}/',{},format='json')
                self.assertEqual(response.status_code,403)
                self.assertEqual(response.json()['error']['code'],'CSRF_FAILED')

    def test_csrf_origin_rejection_even_with_valid_token(self):
        response=self.client.post('/api/v1/auth/logout/',{},format='json',HTTP_ORIGIN='https://outside.example')
        self.assertEqual(response.status_code,403)

    def test_generic_registration_hides_user_and_challenge(self):
        first=self.register();second=self.register()
        self.assertEqual(first.status_code,202)
        self.assertEqual(first.json(),second.json())
        self.assertEqual(set(first.json()['data']),{'message'})
        self.assertEqual(User.objects.filter(email='baru@example.test').count(),1)
        self.assertEqual(len(mail.outbox),1)

    def test_password_hash_and_email_normalization(self):
        self.register('Baru@EXAMPLE.test')
        obj=User.objects.get(email='baru@example.test')
        self.assertNotEqual(obj.password,PASSWORD);self.assertTrue(obj.check_password(PASSWORD))

    def test_role_injection_and_unknown_field_rejected(self):
        response=self.register(role='ADMIN')
        self.assertEqual(response.status_code,400)
        self.assertIn('role',response.json()['error']['fields'])
        self.assertFalse(User.objects.exists())
        response=self.post('auth/register/',[])
        self.assertEqual(response.status_code,400)
        response=self.client.post('/api/v1/auth/login/','email=a',content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,415)

    def test_password_policy_and_confirmation(self):
        for password in ['12345678','password','short']:
            with self.subTest(password=password):
                response=self.post('auth/register/',{'full_name':'Pengguna','email':'policy@example.test',
                    'password':password,'password_confirm':password})
                self.assertEqual(response.status_code,400)
        response=self.post('auth/register/',{'full_name':'Pengguna','email':'policy@example.test',
            'password':PASSWORD,'password_confirm':NEW_PASSWORD})
        self.assertEqual(response.status_code,400)

    def test_challenge_only_in_email_and_digest_only_in_database(self):
        response=self.register();challenge,code=email_challenge()
        otp=EmailOTP.objects.get(pk=challenge)
        self.assertEqual(len(otp.code_digest),64)
        self.assertNotEqual(otp.code_digest,code)
        self.assertNotIn(challenge,response.content.decode());self.assertNotIn(code,response.content.decode())
        self.assertNotIn('code=',mail.outbox[-1].body)
        audit=str(list(AuditEvent.objects.values('before','after')))
        self.assertNotIn(code,audit);self.assertNotIn(PASSWORD,audit)

    def test_verify_is_once_and_does_not_issue_tokens(self):
        self.register();challenge,code=email_challenge()
        data={'challenge_id':challenge,'code':code}
        response=self.post('auth/otp/verify/',data)
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(set(response.json()['data']),{'message'})
        self.assertNotIn(settings.REFRESH_COOKIE_NAME,response.cookies)
        self.assertIsNotNone(User.objects.get(email='baru@example.test').email_verified_at)
        self.assertEqual(self.post('auth/otp/verify/',data).status_code,422)

    def test_wrong_otp_attempt_persists(self):
        self.register();challenge,code=email_challenge()
        wrong='000000' if code!='000000' else '111111'
        response=self.post('auth/otp/verify/',{'challenge_id':challenge,'code':wrong})
        self.assertEqual(response.status_code,422)
        self.assertEqual(EmailOTP.objects.get(pk=challenge).attempt_count,1)

    def test_expired_code_is_rejected(self):
        self.register();challenge,code=email_challenge()
        EmailOTP.objects.filter(pk=challenge).update(created_at=timezone.now()-timedelta(hours=1),expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.post('auth/otp/verify/',{'challenge_id':challenge,'code':code}).status_code,422)
        self.assertIsNone(User.objects.get(email='baru@example.test').email_verified_at)

    def test_otp_purpose_cannot_be_substituted(self):
        self.register();challenge,code=email_challenge()
        response=self.post('auth/password/reset/',{'challenge_id':challenge,'code':code,
            'password':NEW_PASSWORD,'password_confirm':NEW_PASSWORD})
        self.assertEqual(response.status_code,422)
        self.assertTrue(User.objects.get(email='baru@example.test').check_password(PASSWORD))

    def test_resend_revokes_previous_challenge(self):
        self.register();old,code=email_challenge()
        EmailOTP.objects.filter(pk=old).update(resend_after=timezone.now()-timedelta(seconds=1))
        response=self.post('auth/otp/request/',{'email':'baru@example.test','purpose':'EMAIL_VERIFICATION'})
        self.assertEqual(response.status_code,202)
        new,_=email_challenge();self.assertNotEqual(new,old)
        self.assertIsNotNone(EmailOTP.objects.get(pk=old).revoked_at)
        self.assertEqual(self.post('auth/otp/verify/',{'challenge_id':old,'code':code}).status_code,422)

    def test_attempt_counter_survives_resend(self):
        self.register();old,code=email_challenge()
        wrong='000000' if code!='000000' else '111111'
        for _ in range(5):self.assertEqual(self.post('auth/otp/verify/',{'challenge_id':old,'code':wrong}).status_code,422)
        EmailOTP.objects.filter(pk=old).update(resend_after=timezone.now()-timedelta(seconds=1))
        self.post('auth/otp/request/',{'email':'baru@example.test','purpose':'EMAIL_VERIFICATION'})
        new,code=email_challenge()
        response=self.post('auth/otp/verify/',{'challenge_id':new,'code':code})
        self.assertEqual(response.status_code,429)
        self.assertGreaterEqual(int(response['Retry-After']),1)

    def test_otp_request_unknown_and_ineligible_have_same_response(self):
        obj=user()
        unknown=self.post('auth/otp/request/',{'email':'missing@example.test','purpose':'EMAIL_VERIFICATION'})
        known=self.post('auth/otp/request/',{'email':obj.email,'purpose':'EMAIL_VERIFICATION'})
        self.assertEqual(unknown.status_code,202);self.assertEqual(unknown.json(),known.json())
        response=self.post('auth/otp/request/',{'email':obj.email,'purpose':'ACCOUNT_ACTIVATION'})
        self.assertEqual(response.status_code,400)

    @patch('accounts.services.EmailMessage.send',return_value=0)
    def test_public_delivery_failure_remains_generic(self,send):
        response=self.register()
        self.assertEqual(response.status_code,202)
        self.assertEqual(set(response.json()['data']),{'message'})
        self.assertIsNotNone(EmailOTP.objects.get().revoked_at)
        self.assertTrue(AuditEvent.objects.filter(action='OTP_DELIVERY_FAILED').exists())

    def test_local_mailbox_writes_private_email_files(self):
        with tempfile.TemporaryDirectory() as directory,override_settings(EMAIL_BACKEND='common.email_backend.PrivateFileEmailBackend',EMAIL_FILE_PATH=directory):
            self.assertEqual(self.register().status_code,202)
            files=list(Path(directory).glob('*.eml'));self.assertEqual(len(files),1)
            self.assertIn(b'challenge_id=',files[0].read_bytes())
            if os.name!='nt':self.assertEqual(files[0].stat().st_mode & 0o777,0o600)

    def test_unverified_or_wrong_password_cannot_login(self):
        obj=user(verified=False)
        self.assertEqual(self.post('auth/login/',{'email':obj.email,'password':PASSWORD}).status_code,401)
        obj.email_verified_at=timezone.now();obj.save()
        self.assertEqual(self.post('auth/login/',{'email':obj.email,'password':NEW_PASSWORD}).status_code,401)

    def test_login_me_and_cookie_contract(self):
        obj=user();response=self.sign_in(obj)
        self.assertEqual(set(response.json()['data']),{'access'})
        cookie=response.cookies[settings.REFRESH_COOKIE_NAME]
        self.assertTrue(cookie['httponly']);self.assertEqual(cookie['samesite'],'Lax')
        self.assertEqual(cookie['path'],'/api/v1/auth/')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+response.json()['data']['access'])
        response=self.client.get('/api/v1/me/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(set(response.json()['data']),{'id','full_name','email','role','email_verified_at','is_active','effective_permissions'})
        self.assertEqual(response['Cache-Control'],'no-store')

    def test_refresh_rotates_and_rejects_reuse(self):
        obj=user();response=self.sign_in(obj)
        old=response.cookies[settings.REFRESH_COOKIE_NAME].value
        response=self.post('auth/refresh/',{})
        self.assertEqual(response.status_code,200,response.content)
        self.assertNotEqual(response.cookies[settings.REFRESH_COOKIE_NAME].value,old)
        self.client.cookies[settings.REFRESH_COOKIE_NAME]=old
        self.assertEqual(self.post('auth/refresh/',{}).status_code,401)

    def test_refresh_in_body_is_rejected(self):
        response=self.post('auth/refresh/',{'refresh':'body-token'})
        self.assertEqual(response.status_code,400)

    def test_logout_is_204_and_blacklists_refresh(self):
        obj=user();response=self.sign_in(obj);old=response.cookies[settings.REFRESH_COOKIE_NAME].value
        response=self.post('auth/logout/',{})
        self.assertEqual(response.status_code,204);self.assertEqual(response.content,b'')
        self.assertEqual(response.cookies[settings.REFRESH_COOKIE_NAME]['max-age'],0)
        self.client.cookies[settings.REFRESH_COOKIE_NAME]=old
        self.assertEqual(self.post('auth/refresh/',{}).status_code,401)

    def test_reset_atomically_revokes_access_and_refresh(self):
        obj=user();login=self.sign_in(obj);old_access=login.json()['data']['access']
        self.post('auth/otp/request/',{'email':obj.email,'purpose':'PASSWORD_RESET'})
        challenge,code=email_challenge()
        response=self.post('auth/password/reset/',{'challenge_id':challenge,'code':code,
            'password':NEW_PASSWORD,'password_confirm':NEW_PASSWORD})
        self.assertEqual(response.status_code,200,response.content)
        obj.refresh_from_db();self.assertEqual(obj.auth_version,2);self.assertTrue(obj.check_password(NEW_PASSWORD))
        self.assertEqual(self.post('auth/refresh/',{}).status_code,401)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+old_access)
        self.assertEqual(self.client.get('/api/v1/me/').status_code,401)

    def test_invalid_new_password_does_not_consume_challenge(self):
        obj=user();self.post('auth/otp/request/',{'email':obj.email,'purpose':'PASSWORD_RESET'})
        challenge,code=email_challenge()
        response=self.post('auth/password/reset/',{'challenge_id':challenge,'code':code,'password':'12345678','password_confirm':'12345678'})
        self.assertEqual(response.status_code,400)
        self.assertIsNone(EmailOTP.objects.get(pk=challenge).consumed_at)
        obj.refresh_from_db();self.assertEqual(obj.auth_version,1)

    def test_disabled_account_immediately_loses_access(self):
        obj=user();self.bearer(obj)
        User.objects.filter(pk=obj.pk).update(is_active=False)
        self.assertEqual(self.client.get('/api/v1/me/').status_code,401)

    def test_profile_only_accepts_full_name(self):
        obj=user();self.bearer(obj)
        response=self.client.patch('/api/v1/me/',{'role':'ADMIN'},format='json')
        self.assertEqual(response.status_code,400)
        response=self.client.patch('/api/v1/me/',{'full_name':'Nama Baru'},format='json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['data']['full_name'],'Nama Baru')
        self.assertTrue(AuditEvent.objects.filter(action='PROFILE_UPDATED').exists())

    def test_operator_catalog_exactly_seven_integer_ids(self):
        obj=user(role=Role.ADMIN,perms=['manage_operator']);self.bearer(obj)
        response=self.client.get('/api/v1/admin/operator-permissions/')
        self.assertEqual(response.status_code,200,response.content)
        rows=response.json()['results']
        self.assertEqual({x['codename'] for x in rows},set(OPERATOR_PERMISSIONS))
        self.assertTrue(all(isinstance(x['id'],int) for x in rows))

    def test_operator_create_then_activation_uses_explicit_permissions(self):
        admin=user(role=Role.ADMIN,perms=['manage_operator']);self.bearer(admin)
        permission=permission_queryset().get(codename='view_assigned_report')
        response=self.post('admin/operators/',{'full_name':'Operator Baru','email':'operator@example.test','permission_ids':[permission.id]})
        self.assertEqual(response.status_code,201,response.content)
        obj=User.objects.get(email='operator@example.test')
        self.assertFalse(obj.is_active);self.assertFalse(obj.has_usable_password())
        self.assertEqual(response.json()['data']['permission_ids'],[permission.id])
        challenge,code=email_challenge()
        self.client.credentials(HTTP_X_CSRFTOKEN=self.client.get('/api/v1/auth/csrf/').json()['data']['csrf_token'])
        response=self.post('auth/operators/activate/',{'challenge_id':challenge,'code':code,'password':PASSWORD,'password_confirm':PASSWORD})
        self.assertEqual(response.status_code,200,response.content)
        obj.refresh_from_db();self.assertTrue(obj.is_active);self.assertIsNotNone(obj.email_verified_at)

    def test_operator_permissions_cannot_include_admin_or_duplicate(self):
        admin=user(role=Role.ADMIN,perms=['manage_operator']);self.bearer(admin)
        permission=permission_queryset().get(codename='manage_operator')
        response=self.post('admin/operators/',{'full_name':'Operator','email':'op@example.test','permission_ids':[permission.id]})
        self.assertEqual(response.status_code,400)
        permission=permission_queryset().get(codename='view_queue')
        response=self.post('admin/operators/',{'full_name':'Operator','email':'op@example.test','permission_ids':[permission.id,permission.id]})
        self.assertEqual(response.status_code,400)

    def test_admin_role_without_grant_is_denied(self):
        admin=user(role=Role.ADMIN);self.bearer(admin)
        self.assertEqual(self.client.get('/api/v1/admin/operators/').status_code,403)

    def test_permission_revocation_effective_on_existing_token(self):
        admin=user(role=Role.ADMIN,perms=['manage_operator']);self.bearer(admin)
        self.assertEqual(self.client.get('/api/v1/admin/operators/').status_code,200)
        admin.user_permissions.clear()
        self.assertEqual(self.client.get('/api/v1/admin/operators/').status_code,403)

    def test_assignment_projection_omits_email_and_permission_ids(self):
        admin=user(role=Role.ADMIN,perms=['assign_report']);self.bearer(admin)
        user('operator@example.test',role=Role.OPERATOR,perms=['view_assigned_report'])
        user('helperadmin@example.test',role=Role.ADMIN,perms=['view_assigned_report'])
        response=self.client.get('/api/v1/admin/operators/')
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['count'],2)
        self.assertEqual(set(response.json()['results'][0]),{'id','full_name','is_active','email_verified_at','effective_permissions'})
        self.assertEqual(self.client.get('/api/v1/admin/operator-permissions/').status_code,403)

    def test_cannot_activate_unverified_operator_by_admin_patch(self):
        admin=user(role=Role.ADMIN,perms=['manage_operator']);self.bearer(admin)
        obj=user('op@example.test',role=Role.OPERATOR,verified=False,active=False)
        response=self.client.patch(f'/api/v1/admin/operators/{obj.id}/',{'is_active':True},format='json')
        self.assertEqual(response.status_code,422)

    @patch('accounts.services.EmailMessage.send',return_value=0)
    def test_operator_create_survives_delivery_failure_and_resend_is_503(self,send):
        admin=user(role=Role.ADMIN,perms=['manage_operator']);self.bearer(admin)
        response=self.post('admin/operators/',{'full_name':'Operator','email':'op@example.test','permission_ids':[]})
        self.assertEqual(response.status_code,201)
        obj=User.objects.get(email='op@example.test');self.assertFalse(obj.is_active)
        EmailOTP.objects.filter(user=obj).update(resend_after=timezone.now()-timedelta(seconds=1))
        response=self.post(f'admin/operators/{obj.id}/activation-otp/',{})
        self.assertEqual(response.status_code,503,response.content)
        self.assertEqual(response.json()['error']['code'],'OTP_DELIVERY_FAILED')

    def test_unknown_query_and_pagination_rejected(self):
        admin=user(role=Role.ADMIN,perms=['manage_operator']);self.bearer(admin)
        for query in ['role=ADMIN','page_size=101','page=0']:
            self.assertEqual(self.client.get('/api/v1/admin/operators/?'+query).status_code,400)
        self.assertEqual(self.client.get('/api/v1/me/?extra=1').status_code,400)
        self.assertEqual(self.client.get('/api/v1/auth/csrf/?extra=1').status_code,400)

    def test_cors_and_safe_json_errors(self):
        response=self.client.get('/api/v1/me/',HTTP_ORIGIN='http://localhost:5173')
        self.assertEqual(response['Access-Control-Allow-Origin'],'http://localhost:5173')
        self.assertEqual(response['Access-Control-Allow-Credentials'],'true')
        response=self.client.get('/api/v1/not-implemented/')
        self.assertEqual(response.status_code,404)
        self.assertEqual(set(response.json()['error']),{'code','message','fields','request_id'})
        self.assertEqual(response['X-Request-ID'],response.json()['error']['request_id'])
        self.assertEqual(self.client.get('/private_outbox/').status_code,404)
