import uuid
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q, F
from django.db.models.functions import Lower, Trim
from django.utils import timezone

class Role(models.TextChoices):
    REPORTER = 'REPORTER'
    OPERATOR = 'OPERATOR'
    ADMIN = 'ADMIN'

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email wajib diisi.')
        user = self.model(email=email.strip().casefold(), **extra)
        user.set_password(password)
        user.full_clean(exclude=['password'])
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', Role.ADMIN)
        extra.setdefault('email_verified_at', timezone.now())
        if not extra['is_staff'] or not extra['is_superuser']:
            raise ValueError('Superuser memerlukan is_staff dan is_superuser.')
        return self.create_user(email, password, **extra)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(max_length=254, unique=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REPORTER)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    auth_version = models.PositiveIntegerField(default=1)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('email'), name='user_email_ci_unique'),
            models.CheckConstraint(condition=Q(email=Lower(Trim('email'))), name='user_email_normalized'),
            models.CheckConstraint(condition=Q(auth_version__gte=1), name='user_auth_version_positive'),
            models.CheckConstraint(condition=Q(role__in=Role.values), name='user_role_allowed'),
        ]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().casefold()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Akun dinonaktifkan; riwayat tidak dihapus.')

class OTPPurpose(models.TextChoices):
    EMAIL_VERIFICATION = 'EMAIL_VERIFICATION'
    ACCOUNT_ACTIVATION = 'ACCOUNT_ACTIVATION'
    PASSWORD_RESET = 'PASSWORD_RESET'

class EmailOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    purpose = models.CharField(max_length=30, choices=OTPPurpose.choices)
    code_digest = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempt_count = models.PositiveIntegerField(default=0)
    resend_after = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(expires_at__gt=F('created_at')), name='otp_expiry_after_creation'),
            models.CheckConstraint(condition=Q(purpose__in=OTPPurpose.values), name='otp_purpose_allowed'),
            models.UniqueConstraint(fields=['user', 'purpose'], condition=Q(consumed_at__isnull=True, revoked_at__isnull=True), name='otp_one_live_challenge'),
        ]
        indexes = [models.Index(fields=['user', 'purpose', '-created_at'])]

class SecurityThrottle(models.Model):
    """Technical persistent rate counter; not a new business entity."""
    key = models.CharField(max_length=64, primary_key=True)
    window_started_at = models.DateTimeField()
    count = models.PositiveIntegerField(default=0)
