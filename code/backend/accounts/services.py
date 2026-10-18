from datetime import timedelta
import hashlib
import hmac
import secrets
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import EmailMessage
from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from common.api import ApiProblem
from core.audit import record_event
from core.permissions import require_admin, permission_queryset, OPERATOR_PERMISSIONS
from .models import User, Role, EmailOTP, OTPPurpose, SecurityThrottle

GENERIC_MESSAGE='Jika alamat memenuhi syarat, petunjuk dan kode akan dikirim melalui email. Periksa email terbaru Anda.'

def rate_limit(label, identity, *, limit, seconds=900):
    key=hmac.new(settings.OTP_HMAC_KEY.encode(),f'{label}:{identity}'.encode(),hashlib.sha256).hexdigest()
    now=timezone.now()
    blocked=False
    with transaction.atomic():
        SecurityThrottle.objects.get_or_create(key=key,defaults={'window_started_at':now,'count':0})
        counter=SecurityThrottle.objects.select_for_update().get(pk=key)
        if now-counter.window_started_at>=timedelta(seconds=seconds):
            counter.window_started_at,counter.count=now,0
        if counter.count>=limit:
            blocked=True
            wait=max(1,(counter.window_started_at+timedelta(seconds=seconds)-now).total_seconds())
        else:
            counter.count+=1
            counter.save()
    if blocked:
        raise ApiProblem('RATE_LIMITED','Terlalu banyak percobaan. Coba kembali nanti.',429,retry_after=wait)

def validate_new_password(password,user):
    try:validate_password(password,user)
    except DjangoValidationError as e:raise ValidationError({'password':e.messages})

def _digest(otp,code):
    message=f'{otp.id}:{otp.user_id}:{otp.purpose}:{code}'
    return hmac.new(settings.OTP_HMAC_KEY.encode(),message.encode(),hashlib.sha256).hexdigest()

def dispatch_otp(user,purpose,*,actor=None,request_id=None,admin_dispatch=False):
    now=timezone.now()
    with transaction.atomic():
        user=User.objects.select_for_update().get(pk=user.pk)
        eligible=(purpose==OTPPurpose.ACCOUNT_ACTIVATION and user.role==Role.OPERATOR and not user.email_verified_at
                  or purpose==OTPPurpose.EMAIL_VERIFICATION and user.role==Role.REPORTER and not user.email_verified_at and user.is_active
                  or purpose==OTPPurpose.PASSWORD_RESET and user.is_active and user.email_verified_at)
        if not eligible:
            if admin_dispatch:raise ApiProblem('ACTIVATION_NOT_ALLOWED','Akun sudah menyelesaikan aktivasi atau tidak memenuhi syarat.',422)
            return None
        recent=EmailOTP.objects.filter(user=user,purpose=purpose).order_by('-created_at').first()
        if recent and now<recent.resend_after:
            if admin_dispatch:
                raise ApiProblem('RATE_LIMITED','Tunggu sebelum mengirim ulang.',429,retry_after=(recent.resend_after-now).total_seconds())
            return None
        EmailOTP.objects.filter(user=user,purpose=purpose,consumed_at__isnull=True,revoked_at__isnull=True).update(revoked_at=now)
        code=f'{secrets.randbelow(1_000_000):06d}'
        otp=EmailOTP(user=user,purpose=purpose,expires_at=now+timedelta(seconds=settings.OTP_TTL_SECONDS),resend_after=now+timedelta(seconds=settings.OTP_RESEND_SECONDS))
        otp.code_digest=_digest(otp,code)
        otp.save()
        record_event(actor=actor,action='OTP_DISPATCH_PREPARED',object_type='EmailOTP',object_id=otp.id,
                     after={'purpose':purpose},request_id=request_id)
    path={OTPPurpose.EMAIL_VERIFICATION:settings.FRONTEND_VERIFY_PATH,
          OTPPurpose.ACCOUNT_ACTIVATION:settings.FRONTEND_ACTIVATE_PATH,
          OTPPurpose.PASSWORD_RESET:settings.FRONTEND_RESET_PATH}[purpose]
    url=f'{settings.FRONTEND_URL}{path}?{urlencode({"challenge_id":str(otp.id)})}'
    body=(f'Permintaan akun SILAR: {purpose}\n\nKode enam digit: {code}\n'
          f'Buka halaman aplikasi: {url}\n\nKode berlaku sampai {otp.expires_at.isoformat()}. '
          'Kode sekali pakai. Jaga kerahasiaan kode dan password. Abaikan email bila Anda tidak meminta tindakan ini.')
    try:
        sent=EmailMessage('Kode akun SILAR',body,settings.DEFAULT_FROM_EMAIL,[user.email]).send(fail_silently=False)
        if not sent:raise RuntimeError('delivery unavailable')
    except Exception:
        with transaction.atomic():
            EmailOTP.objects.filter(pk=otp.pk,consumed_at__isnull=True).update(revoked_at=timezone.now())
            record_event(actor=actor,action='OTP_DELIVERY_FAILED',object_type='EmailOTP',object_id=otp.id,
                         after={'error_code':'OTP_DELIVERY_FAILED'},request_id=request_id)
        if admin_dispatch:raise ApiProblem('OTP_DELIVERY_FAILED','Pengiriman aktivasi belum berhasil. Akun tetap belum aktif.',503)
        return None
    return otp

def register(data,request_id=None):
    email=data['email'].strip().casefold()
    candidate=User(email=email,full_name=data['full_name'],role=Role.REPORTER)
    validate_new_password(data['password'],candidate)
    with transaction.atomic():
        user=User.objects.filter(email=email).first()
        if user is None:
            candidate.set_password(data['password'])
            try:
                with transaction.atomic():candidate.save(force_insert=True)
                user=candidate
                record_event(actor=user,action='ACCOUNT_REGISTERED',object_type='User',object_id=user.id,
                             after={'role':Role.REPORTER},request_id=request_id)
            except IntegrityError:
                user=User.objects.get(email=email)
    if user.role==Role.REPORTER and user.is_active and not user.email_verified_at:
        dispatch_otp(user,OTPPurpose.EMAIL_VERIFICATION,request_id=request_id)
    return {'message':GENERIC_MESSAGE}

def request_otp(email,purpose,request_id=None):
    user=User.objects.filter(email=email.strip().casefold()).first()
    if user:dispatch_otp(user,purpose,request_id=request_id)
    return {'message':GENERIC_MESSAGE}

def consume_otp(challenge_id,code,purpose,*,password=None,request_id=None):
    initial=EmailOTP.objects.filter(pk=challenge_id).values('user_id').first()
    if not initial:raise ApiProblem('OTP_INVALID','Kode tidak dapat digunakan. Periksa email terbaru.',422)
    error=None
    with transaction.atomic():
        user=User.objects.select_for_update().get(pk=initial['user_id'])
        otp=EmailOTP.objects.select_for_update().get(pk=challenge_id)
        now=timezone.now()
        valid=(otp.purpose==purpose and not otp.consumed_at and not otp.revoked_at
               and now<otp.expires_at and otp.attempt_count<settings.OTP_MAX_ATTEMPTS)
        if not valid or not hmac.compare_digest(otp.code_digest,_digest(otp,code)):
            if not otp.consumed_at and not otp.revoked_at:
                otp.attempt_count+=1
                if otp.attempt_count>=settings.OTP_MAX_ATTEMPTS:otp.revoked_at=now
                otp.save(update_fields=['attempt_count','revoked_at'])
            error=ApiProblem('OTP_INVALID','Kode tidak dapat digunakan. Periksa email terbaru.',422)
        elif purpose==OTPPurpose.ACCOUNT_ACTIVATION and (user.role!=Role.OPERATOR or user.email_verified_at):
            error=ApiProblem('ACTIVATION_NOT_ALLOWED','Akun tidak memenuhi syarat aktivasi.',422)
        elif purpose==OTPPurpose.EMAIL_VERIFICATION and (not user.is_active or user.role!=Role.REPORTER):
            error=ApiProblem('OTP_INVALID','Kode tidak dapat digunakan.',422)
        elif purpose==OTPPurpose.PASSWORD_RESET and (not user.is_active or not user.email_verified_at):
            error=ApiProblem('OTP_INVALID','Kode tidak dapat digunakan.',422)
        else:
            if password is not None:
                validate_new_password(password,user)
                user.set_password(password)
            if purpose in (OTPPurpose.EMAIL_VERIFICATION,OTPPurpose.ACCOUNT_ACTIVATION):
                user.email_verified_at=now
            if purpose==OTPPurpose.ACCOUNT_ACTIVATION:user.is_active=True
            if purpose==OTPPurpose.PASSWORD_RESET:
                user.auth_version+=1
                for token in OutstandingToken.objects.filter(user=user):
                    BlacklistedToken.objects.get_or_create(token=token)
            user.save()
            otp.consumed_at=now;otp.save(update_fields=['consumed_at'])
            record_event(actor=user,action='ACCOUNT_'+purpose,object_type='User',object_id=user.id,
                         after={'purpose':purpose,'email_verified':bool(user.email_verified_at)},request_id=request_id)
    if error:raise error
    return {'message':'Tindakan akun berhasil. Silakan masuk.'}

def issue_tokens(user):
    token=RefreshToken.for_user(user)
    token['auth_version']=user.auth_version
    OutstandingToken.objects.filter(jti=token['jti']).update(token=str(token))
    return str(token.access_token),str(token)

def login(email,password,request_id=None):
    email=email.strip().casefold()
    user=authenticate(email=email,password=password)
    if not user or not user.email_verified_at:
        raise ApiProblem('INVALID_CREDENTIALS','Email atau password tidak dapat digunakan.',401)
    with transaction.atomic():
        user=User.objects.select_for_update().get(pk=user.pk)
        if not user.is_active or not user.check_password(password):
            raise ApiProblem('INVALID_CREDENTIALS','Email atau password tidak dapat digunakan.',401)
        tokens=issue_tokens(user)
        record_event(actor=user,action='ACCOUNT_LOGIN',object_type='User',object_id=user.id,request_id=request_id)
    return tokens

def rotate_refresh(raw,request_id=None):
    try:token=RefreshToken(raw)
    except (TokenError,TypeError):raise ApiProblem('TOKEN_INVALID','Sesi tidak dapat digunakan.',401)
    with transaction.atomic():
        user=User.objects.select_for_update().filter(pk=token.get('user_id')).first()
        if not user or not user.is_active or not user.email_verified_at or token.get('auth_version')!=user.auth_version:
            raise ApiProblem('TOKEN_INVALID','Sesi tidak dapat digunakan.',401)
        outstanding=OutstandingToken.objects.select_for_update().filter(jti=token['jti'],user=user).first()
        if not outstanding or BlacklistedToken.objects.filter(token=outstanding).exists():
            raise ApiProblem('TOKEN_INVALID','Sesi tidak dapat digunakan.',401)
        BlacklistedToken.objects.create(token=outstanding)
        tokens=issue_tokens(user)
        record_event(actor=user,action='ACCOUNT_REFRESH',object_type='User',object_id=user.id,request_id=request_id)
    return tokens

def logout(raw,request_id=None):
    if not raw:return
    try:token=RefreshToken(raw)
    except (TokenError,TypeError):return
    with transaction.atomic():
        user=User.objects.select_for_update().filter(pk=token.get('user_id')).first()
        if not user:return
        outstanding=OutstandingToken.objects.select_for_update().filter(jti=token['jti'],user=user).first()
        if outstanding:BlacklistedToken.objects.get_or_create(token=outstanding)
        record_event(actor=user,action='ACCOUNT_LOGOUT',object_type='User',object_id=user.id,request_id=request_id)

def operator_permission_ids(ids):
    if len(set(ids))!=len(ids):raise ValidationError({'permission_ids':['ID izin tidak boleh duplikat.']})
    permissions=list(permission_queryset().filter(pk__in=ids,codename__in=OPERATOR_PERMISSIONS))
    if len(permissions)!=len(ids):raise ValidationError({'permission_ids':['Gunakan ID dari katalog tujuh izin Operator.']})
    return permissions

def create_operator(actor,data,request_id=None):
    require_admin(actor,'manage_operator')
    permissions=operator_permission_ids(data['permission_ids'])
    with transaction.atomic():
        try:
            with transaction.atomic():
                user=User.objects.create_user(data['email'],None,full_name=data['full_name'],role=Role.OPERATOR,is_active=False)
        except (IntegrityError,DjangoValidationError):raise ValidationError({'email':['Akun tidak dapat dibuat dengan email ini.']})
        user.user_permissions.set(permissions)
        record_event(actor=actor,action='OPERATOR_CREATED',object_type='User',object_id=user.id,
                     after={'role':Role.OPERATOR,'is_active':False,'permission_ids':data['permission_ids']},request_id=request_id)
    dispatch_otp(user,OTPPurpose.ACCOUNT_ACTIVATION,actor=actor,request_id=request_id)
    return user

def patch_operator(actor,user_id,data,request_id=None):
    require_admin(actor,'manage_operator')
    from django.http import Http404
    with transaction.atomic():
        user=User.objects.select_for_update().filter(pk=user_id,role=Role.OPERATOR).first()
        if not user:raise Http404
        if data.get('is_active') and not user.email_verified_at:
            raise ApiProblem('ACTIVATION_NOT_ALLOWED','Pemilik perlu menyelesaikan aktivasi melalui email.',422)
        if 'permission_ids' in data:
            permissions=operator_permission_ids(data['permission_ids'])
            user.groups.clear()
            user.user_permissions.set(permissions)
        for field in ('full_name','is_active'):
            if field in data:setattr(user,field,data[field])
        user.save()
        record_event(actor=actor,action='OPERATOR_UPDATED',object_type='User',object_id=user.id,
                     after={'changed_fields':sorted(data),'is_active':user.is_active},request_id=request_id)
    return user
