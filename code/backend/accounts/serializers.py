from rest_framework import serializers
from common.api import StrictSerializer
from .models import OTPPurpose

class EmptyBody(StrictSerializer):
    pass

class Register(StrictSerializer):
    full_name=serializers.CharField(max_length=150,trim_whitespace=True)
    email=serializers.EmailField(max_length=254)
    password=serializers.CharField(write_only=True,trim_whitespace=False,max_length=1024)
    password_confirm=serializers.CharField(write_only=True,trim_whitespace=False,max_length=1024)
    def validate(self,attrs):
        if attrs['password']!=attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm':['Konfirmasi password berbeda.']})
        return attrs

class Login(StrictSerializer):
    email=serializers.EmailField(max_length=254)
    password=serializers.CharField(trim_whitespace=False,max_length=1024,write_only=True)

class RequestOTP(StrictSerializer):
    email=serializers.EmailField(max_length=254)
    purpose=serializers.ChoiceField(choices=[OTPPurpose.EMAIL_VERIFICATION,OTPPurpose.PASSWORD_RESET])

class VerifyEmail(StrictSerializer):
    challenge_id=serializers.UUIDField()
    code=serializers.RegexField(r'^[0-9]{6}$',trim_whitespace=False,write_only=True)

class SetPasswordOTP(VerifyEmail):
    password=serializers.CharField(trim_whitespace=False,max_length=1024,write_only=True)
    password_confirm=serializers.CharField(trim_whitespace=False,max_length=1024,write_only=True)
    def validate(self,attrs):
        if attrs['password']!=attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm':['Konfirmasi password berbeda.']})
        return attrs

class ProfilePatch(StrictSerializer):
    full_name=serializers.CharField(max_length=150,trim_whitespace=True)

class OperatorCreate(StrictSerializer):
    full_name=serializers.CharField(max_length=150,trim_whitespace=True)
    email=serializers.EmailField(max_length=254)
    permission_ids=serializers.ListField(child=serializers.IntegerField(min_value=1),allow_empty=True)

class OperatorPatch(StrictSerializer):
    reason=serializers.CharField(max_length=1500,trim_whitespace=True,required=False)
    full_name=serializers.CharField(max_length=150,trim_whitespace=True,required=False)
    is_active=serializers.BooleanField(required=False)
    permission_ids=serializers.ListField(child=serializers.IntegerField(min_value=1),required=False,allow_empty=True)
    def validate(self,attrs):
        if not set(attrs)-{'reason'}:raise serializers.ValidationError('Minimal satu field perubahan diperlukan.')
        return attrs

def account_data(user,operator=False,target=False):
    from core.permissions import effective_permissions,permission_queryset,OPERATOR_PERMISSIONS
    from django.db.models import Q
    data={'id':str(user.id),'full_name':user.full_name,'is_active':user.is_active,
          'email_verified_at':user.email_verified_at,'effective_permissions':sorted(effective_permissions(user))}
    if target:return data
    data.update(email=user.email,role=user.role)
    if operator:
        data['permission_ids']=list(permission_queryset().filter(codename__in=OPERATOR_PERMISSIONS).filter(Q(user=user)|Q(group__user=user)).values_list('id',flat=True).distinct().order_by('id'))
    return data

