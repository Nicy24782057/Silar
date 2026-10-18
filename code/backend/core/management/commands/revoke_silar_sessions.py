from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken,BlacklistedToken
from accounts.models import User
from core.audit import record_event

class Command(BaseCommand):
    help='Cabut seluruh sesi akun melalui pengelola tepercaya, dengan audit SYSTEM.'
    def add_arguments(self,parser):parser.add_argument('email')
    def handle(self,*args,**options):
        with transaction.atomic():
            user=User.objects.select_for_update().filter(email=options['email'].strip().casefold()).first()
            if not user:raise CommandError('Akun tidak tersedia.')
            user.auth_version+=1;user.save(update_fields=['auth_version','updated_at'])
            for token in OutstandingToken.objects.filter(user=user):BlacklistedToken.objects.get_or_create(token=token)
            record_event(actor=None,action='ACCOUNT_SESSIONS_REVOKED',object_type='User',object_id=user.id)
        self.stdout.write(self.style.SUCCESS('Seluruh sesi lama dicabut.'))
