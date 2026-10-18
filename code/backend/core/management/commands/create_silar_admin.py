import getpass
from django.core.management import call_command
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone
from accounts.models import User,Role
from accounts.services import validate_new_password
from core.audit import record_event

class Command(BaseCommand):
    help='Buat Admin aplikasi secara lokal dengan password yang dipilih sendiri.'
    def add_arguments(self,parser):
        parser.add_argument('--email')
        parser.add_argument('--name')
        parser.add_argument('--grant-private',action='store_true')
        parser.add_argument('--grant-operator',action='store_true')
    def handle(self,*args,**options):
        email=(options['email'] or input('Email Admin: ')).strip().casefold()
        name=options['name'] or input('Nama lengkap: ').strip()
        if User.objects.filter(email=email).exists():raise CommandError('Email sudah ada. Tidak ada akun/password yang ditimpa.')
        password=getpass.getpass('Password Admin baru: ')
        if password!=getpass.getpass('Ulangi password: '):raise CommandError('Konfirmasi password berbeda.')
        user=User(email=email,full_name=name,role=Role.ADMIN,email_verified_at=timezone.now())
        try:validate_new_password(password,user)
        except Exception:raise CommandError('Password tidak memenuhi validator; gunakan password kuat yang berbeda dari identitas akun.')
        call_command('bootstrap_silar',verbosity=0)
        with transaction.atomic():
            user.set_password(password);user.full_clean();user.save()
            user.groups.add(Group.objects.get(name='SILAR_ADMIN'))
            if options['grant_private']:
                from core.permissions import permission_queryset
                user.user_permissions.add(permission_queryset().get(codename='view_private_evidence'))
            if options['grant_operator']:user.groups.add(Group.objects.get(name='SILAR_OPERATOR'))
            record_event(actor=None,action='ADMIN_BOOTSTRAPPED',object_type='User',object_id=user.id,
                         after={'role':'ADMIN','is_active':True})
        self.stdout.write(self.style.SUCCESS('Admin dibuat. Masuk melalui API/antarmuka akun; tidak ada password bawaan.'))

