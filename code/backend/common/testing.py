"""Test fixtures only; never used by runtime views or seed commands."""
import re
from django.core import mail
from django.utils import timezone
from accounts.models import User,Role
from core.permissions import permission_queryset

PASSWORD='Rakit!92Sungai#Awan'
NEW_PASSWORD='Ganti!74Batu#Daun'

def user(email='reporter@example.test',role=Role.REPORTER,verified=True,active=True,perms=()):
    obj=User.objects.create_user(email,PASSWORD,full_name='Penguji SILAR',role=role,
        is_active=active,email_verified_at=timezone.now() if verified else None)
    obj.user_permissions.set(permission_queryset().filter(codename__in=perms))
    return obj

def email_challenge():
    body=mail.outbox[-1].body
    return re.search(r'challenge_id=([a-f0-9-]{36})',body).group(1),re.search(r'Kode enam digit: (\d{6})',body).group(1)
