from datetime import timedelta
import json
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from accounts import services
from accounts.models import EmailOTP, OTPPurpose, Role, User
from common.testing import user, email_challenge, PASSWORD, NEW_PASSWORD
from core.models import AuditEvent

class AccountCodeFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):call_command('bootstrap_silar',verbosity=0)
    def setUp(self):
        self.client=APIClient(enforce_csrf_checks=True)
        token=self.client.get('/api/v1/auth/csrf/').data['data']['csrf_token']
        self.client.credentials(HTTP_X_CSRFTOKEN=token)
    def post(self,path,body,**kwargs):return self.client.post('/api/v1/auth/'+path,body,format='json',**kwargs)
    def issue(self,obj,purpose):
        services.dispatch_otp(obj,purpose)
        identifier,code=email_challenge()
        return EmailOTP.objects.get(pk=identifier),code
    def verify(self,obj,code,**kwargs):return self.post('account/verify/',{'email':obj.email.upper(),'code':code},**kwargs)
    def pending(self,email='operator@example.test'):
        return user(email,role=Role.OPERATOR,verified=False,active=False)
    def finish(self,token,password=NEW_PASSWORD):
        return self.post('operators/activate/',{'activation_token':token,'password':password,'password_confirm':password})
    def test_reporter_verifies_by_email_and_code_without_link_or_login(self):
        obj=user(verified=False)
        otp,code=self.issue(obj,OTPPurpose.EMAIL_VERIFICATION)
        result=self.verify(obj,code)
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(result.data['data']['next'],'LOGIN')
        self.assertEqual(set(result.data['data']),{'next','message'})
        self.assertNotIn(settings.REFRESH_COOKIE_NAME,result.cookies)
        obj.refresh_from_db();otp.refresh_from_db()
        self.assertIsNotNone(obj.email_verified_at);self.assertIsNotNone(otp.consumed_at)
        self.assertEqual(obj.role,Role.REPORTER)
        self.assertEqual(self.verify(obj,code).status_code,422)
    def test_operator_proof_is_one_use_and_does_not_activate_before_password(self):
        obj=self.pending();otp,code=self.issue(obj,OTPPurpose.ACCOUNT_ACTIVATION)
        result=self.verify(obj,code)
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(result.data['data']['next'],'SET_PASSWORD')
        token=result.data['data']['activation_token']
        obj.refresh_from_db();otp.refresh_from_db()
        self.assertFalse(obj.is_active);self.assertIsNone(obj.email_verified_at)
        self.assertIsNotNone(otp.consumed_at);self.assertNotIn(token,otp.activation_digest)
        self.assertEqual(self.verify(obj,code).status_code,422)
        activated=self.finish(token)
        self.assertEqual(activated.status_code,200,activated.data)
        obj.refresh_from_db();self.assertTrue(obj.is_active);self.assertTrue(obj.check_password(NEW_PASSWORD))
        self.assertEqual(obj.role,Role.OPERATOR)
        self.assertEqual(self.finish(token).status_code,422)
        audit=json.dumps(list(AuditEvent.objects.values('before','after')))
        self.assertNotIn(token,audit);self.assertNotIn(code,audit);self.assertNotIn(NEW_PASSWORD,audit)
    def test_invalid_password_keeps_proof_available_for_a_corrected_password(self):
        obj=self.pending();_,code=self.issue(obj,OTPPurpose.ACCOUNT_ACTIVATION)
        token=self.verify(obj,code).data['data']['activation_token']
        bad=self.finish(token,'Short!123')
        self.assertEqual(bad.status_code,400,bad.data)
        self.assertEqual(self.finish(token).status_code,200)
    def test_resend_revokes_an_unused_operator_proof(self):
        obj=self.pending();otp,code=self.issue(obj,OTPPurpose.ACCOUNT_ACTIVATION)
        token=self.verify(obj,code).data['data']['activation_token']
        EmailOTP.objects.filter(pk=otp.pk).update(resend_after=timezone.now()-timedelta(seconds=1))
        resent=self.post('otp/request/',{'email':obj.email,'purpose':'ACCOUNT_VERIFICATION'})
        self.assertEqual(resent.status_code,202,resent.data)
        otp.refresh_from_db();self.assertIsNotNone(otp.revoked_at)
        self.assertEqual(self.finish(token).status_code,422)
    def test_proof_expiry_auth_version_and_tampering_are_checked(self):
        for variation in ('expiry','version','tamper'):
            with self.subTest(variation=variation):
                obj=self.pending(variation+'@example.test');otp,code=self.issue(obj,OTPPurpose.ACCOUNT_ACTIVATION)
                token=self.verify(obj,code).data['data']['activation_token']
                if variation=='expiry':
                    EmailOTP.objects.filter(pk=otp.pk).update(created_at=timezone.now()-timedelta(hours=2),expires_at=timezone.now()-timedelta(seconds=1))
                elif variation=='version':User.objects.filter(pk=obj.pk).update(auth_version=2)
                else:token=token[:-1]+('A' if token[-1]!='A' else 'B')
                self.assertEqual(self.finish(token).status_code,422)
                obj.refresh_from_db();self.assertFalse(obj.is_active)
    def test_wrong_purpose_other_email_and_forged_role_do_not_activate(self):
        reporter=user(verified=False)
        _,code=self.issue(reporter,OTPPurpose.EMAIL_VERIFICATION)
        forged=self.post('account/verify/',{'email':reporter.email,'code':code,'role':'OPERATOR'})
        self.assertEqual(forged.status_code,400)
        other=self.pending();self.assertEqual(self.verify(other,code).status_code,422)
        active=user('active@example.test');otp,reset_code=self.issue(active,OTPPurpose.PASSWORD_RESET)
        self.assertEqual(self.verify(active,reset_code).status_code,422)
        otp.refresh_from_db();self.assertIsNone(otp.consumed_at)
        result=self.verify(reporter,code)
        self.assertEqual(result.data['data']['next'],'LOGIN');self.assertNotIn('activation_token',result.data['data'])
    def test_unknown_and_ineligible_emails_have_generic_resend_and_error(self):
        verified=user()
        pending=self.pending();services.dispatch_otp(pending,OTPPurpose.ACCOUNT_ACTIVATION)
        responses=[self.post('otp/request/',{'email':email,'purpose':'ACCOUNT_VERIFICATION'}) for email in
                   ('missing@example.test',verified.email,pending.email)]
        self.assertEqual([r.status_code for r in responses],[202]*3)
        self.assertTrue(all(r.data==responses[0].data for r in responses))
        errors=[self.post('account/verify/',{'email':email,'code':'000000'}) for email in ('missing@example.test',verified.email)]
        self.assertTrue(all(r.status_code==422 and r.data['error']['code']=='OTP_INVALID' for r in errors))
    def test_attempt_limit_survives_resend_ip_change_and_legacy_endpoint(self):
        obj=user(verified=False);otp,code=self.issue(obj,OTPPurpose.EMAIL_VERIFICATION)
        wrong='000000' if code!='000000' else '000001'
        legacy=self.post('otp/verify/',{'challenge_id':str(otp.pk),'code':wrong})
        self.assertEqual(legacy.status_code,422)
        for attempt in range(4):
            if attempt==2:
                EmailOTP.objects.filter(pk=otp.pk).update(resend_after=timezone.now()-timedelta(seconds=1))
                self.post('otp/request/',{'email':obj.email,'purpose':'ACCOUNT_VERIFICATION'})
                identifier,code=email_challenge();otp=EmailOTP.objects.get(pk=identifier)
                wrong='000000' if code!='000000' else '000001'
            self.assertEqual(self.verify(obj,wrong,REMOTE_ADDR='127.0.0.'+str(attempt+2)).status_code,422)
        blocked=self.verify(obj,code,REMOTE_ADDR='127.0.0.9')
        self.assertEqual(blocked.status_code,429,blocked.data)
        self.assertGreater(int(blocked['Retry-After']),0)
        obj.refresh_from_db();self.assertIsNone(obj.email_verified_at)
    def test_code_expires_and_cannot_be_used_after_window(self):
        obj=user(verified=False);otp,code=self.issue(obj,OTPPurpose.EMAIL_VERIFICATION)
        with patch('accounts.services.timezone.now',return_value=otp.expires_at+timedelta(seconds=1)):
            self.assertEqual(self.verify(obj,code).status_code,422)
        obj.refresh_from_db();self.assertIsNone(obj.email_verified_at)
    def test_account_policy_has_no_account_or_secret_and_auth_post_requires_csrf(self):
        policy=APIClient().get('/api/v1/auth/account-policy/')
        self.assertEqual(policy.status_code,200)
        self.assertEqual(policy.data['data'],{'password_min_length':15,'otp_resend_seconds':60,'otp_ttl_seconds':600,'otp_max_attempts':5,'otp_window_seconds':900})
        self.assertEqual(APIClient(enforce_csrf_checks=True).post('/api/v1/auth/account/verify/',{},format='json').status_code,403)
    def test_email_contains_clear_code_and_optional_link_for_both_roles(self):
        for obj,purpose in [(user(verified=False),OTPPurpose.EMAIL_VERIFICATION),(self.pending(),OTPPurpose.ACCOUNT_ACTIVATION)]:
            _,code=self.issue(obj,purpose)
            self.assertIn('Kode enam digit: '+code,mail.outbox[-1].body)
            self.assertIn('tautan',mail.outbox[-1].body.lower())
            self.assertTrue(mail.outbox[-1].alternatives)
            self.assertNotIn('password=',mail.outbox[-1].body)
    def test_registration_rejects_short_password_and_sends_code_for_valid_one(self):
        body={'email':'new@example.test','full_name':'Pengguna Baru','password':'Masihpendek12!','password_confirm':'Masihpendek12!'}
        self.assertEqual(self.post('register/',body).status_code,400)
        body.update(password=PASSWORD,password_confirm=PASSWORD)
        self.assertEqual(self.post('register/',body).status_code,202)
        identifier,code=email_challenge()
        self.assertNotIn(identifier,self.post('otp/request/',{'email':body['email'],'purpose':'ACCOUNT_VERIFICATION'}).content.decode())
        self.assertEqual(self.post('account/verify/',{'email':body['email'],'code':code}).status_code,200)

class PasswordPolicyTests(SimpleTestCase):
    def test_predictable_identity_repetition_and_keyboard_passwords_are_rejected(self):
        account=User(email='john@example.test',full_name='John')
        for value in ('John','John123','John 123','John!2026','John123456789012345','J0hn1234567890123',
                      'aaaaaaaaaaaaaaaa','abcdabcdabcdabcd','123456789012345','qwertyuiopasdfgh',
                      'Password123456789!','SILAR12345678901!','P@ssw0rd123456789','S1LAR1234567890!'):
            with self.subTest(value=value),self.assertRaises(ValidationError):validate_password(value,account)
    def test_passphrases_and_random_passwords_do_not_need_a_character_mixture(self):
        account=User(email='john@example.test',full_name='John')
        for value in ('kabut bambu sungai merpati','John memilih bambu dan awan',PASSWORD,NEW_PASSWORD,'!@#$%^&*()-_=+?/:<>'):
            with self.subTest(value=value):validate_password(value,account)

from concurrent.futures import ThreadPoolExecutor
from django.db import close_old_connections, connections, connection
from django.test import TransactionTestCase

class AccountCodeConcurrencyTests(TransactionTestCase):
    def setUp(self):
        if connection.vendor!='postgresql':raise RuntimeError('Pengujian kode serentak memerlukan PostgreSQL 16.')
        call_command('bootstrap_silar',verbosity=0)
    def parallel(self,work):
        def invoke(_):
            close_old_connections()
            try:
                work()
                return 200
            except services.ApiProblem as error:return error.status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:return sorted(pool.map(invoke,range(2)))
    def test_two_reporter_verifications_consume_one_code_and_record_one_event(self):
        obj=user(verified=False);services.dispatch_otp(obj,OTPPurpose.EMAIL_VERIFICATION)
        _,code=email_challenge()
        self.assertEqual(self.parallel(lambda:services.verify_account(obj.email,code)),[200,422])
        self.assertEqual(AuditEvent.objects.filter(actor=obj,action='ACCOUNT_EMAIL_VERIFICATION').count(),1)
    def test_operator_code_and_activation_proof_each_have_only_one_winner(self):
        obj=user(role=Role.OPERATOR,verified=False,active=False)
        services.dispatch_otp(obj,OTPPurpose.ACCOUNT_ACTIVATION);identifier,code=email_challenge()
        proofs=[]
        def verify():proofs.append(services.verify_account(obj.email,code)['activation_token'])
        self.assertEqual(self.parallel(verify),[200,422]);self.assertEqual(len(proofs),1)
        self.assertEqual(self.parallel(lambda:services.finish_activation(proofs[0],NEW_PASSWORD)),[200,422])
        self.assertEqual(AuditEvent.objects.filter(actor=obj,action='ACCOUNT_ACCOUNT_ACTIVATION').count(),1)
