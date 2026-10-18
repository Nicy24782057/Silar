from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group,Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from core.models import Report
from core.permissions import OPERATOR_PERMISSIONS,ADMIN_PERMISSIONS

class Command(BaseCommand):
    help='Menyiapkan Group/Permission A5.7; tidak membuat akun/password demo.'
    def handle(self,*args,**options):
        with transaction.atomic():
            ct=ContentType.objects.get_for_model(Report)
            permissions={}
            for code,label in Report._meta.permissions:
                p,_=Permission.objects.get_or_create(content_type=ct,codename=code,defaults={'name':label})
                permissions[code]=p
            for name,codes in [('SILAR_REPORTER',()),('SILAR_OPERATOR',OPERATOR_PERMISSIONS),
                               ('SILAR_ADMIN',tuple(x for x in ADMIN_PERMISSIONS if x!='view_private_evidence'))]:
                group,_=Group.objects.get_or_create(name=name)
                group.permissions.set([permissions[x] for x in codes])
        self.stdout.write(self.style.SUCCESS('Katalog 13 izin dan tiga Group tersedia. Izin Operator/Admin tetap diberikan eksplisit.'))

