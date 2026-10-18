from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework.views import APIView
from common.api import AuthAPIView,ApiProblem,validate_query,reject_query
from core.audit import record_event
from core.permissions import require_admin,effective_permissions,permission_queryset,OPERATOR_PERMISSIONS
from . import serializers as S, services
from .models import User,Role,OTPPurpose

def validated(serializer_class,request):
    reject_query(request)
    serializer=serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data

def throttle(request,action,identity=''):
    # REMOTE_ADDR is authoritative here; never trust arbitrary X-Forwarded-For.
    ip=request.META.get('REMOTE_ADDR','unknown')
    services.rate_limit('auth-ip',ip,limit=100,seconds=900)
    if action in ('register','otp-request'):
        services.rate_limit('otp-send',identity,limit=settings.OTP_SEND_LIMIT,seconds=settings.OTP_WINDOW_SECONDS)
    elif action in ('verify','activate','reset'):
        services.rate_limit('otp-check',identity,limit=settings.OTP_MAX_ATTEMPTS,seconds=settings.OTP_WINDOW_SECONDS)
    elif action=='login':
        services.rate_limit('login',ip+':'+identity,limit=20,seconds=900)

def token_response(access,refresh):
    response=Response({'data':{'access':access}})
    response.set_cookie(settings.REFRESH_COOKIE_NAME,refresh,
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        path=settings.REFRESH_COOKIE_PATH,secure=not settings.SILAR_LOCAL_MODE,httponly=True,samesite='Lax')
    return response

class CSRFView(AuthAPIView):
    def get(self,request):
        return Response({'data':{'csrf_token':get_token(request._request)}})

class RegisterView(AuthAPIView):
    def post(self,request):
        data=validated(S.Register,request)
        throttle(request,'register',data['email'].strip().casefold()+':EMAIL_VERIFICATION')
        return Response({'data':services.register(data,request.request_id)},status=202)

class OTPRequestView(AuthAPIView):
    def post(self,request):
        data=validated(S.RequestOTP,request)
        throttle(request,'otp-request',data['email'].strip().casefold()+':'+data['purpose'])
        return Response({'data':services.request_otp(data['email'],data['purpose'],request.request_id)},status=202)

class OTPVerifyView(AuthAPIView):
    purpose=OTPPurpose.EMAIL_VERIFICATION
    serializer_class=S.VerifyEmail
    action='verify'
    def post(self,request):
        data=validated(self.serializer_class,request)
        # A user/purpose counter survives resend across challenge IDs.
        from .models import EmailOTP
        target=EmailOTP.objects.filter(pk=data['challenge_id']).values('user_id').first()
        identity=str(target['user_id']) if target else 'unknown:'+request.META.get('REMOTE_ADDR','unknown')
        throttle(request,self.action,identity+':'+self.purpose)
        result=services.consume_otp(data['challenge_id'],data['code'],self.purpose,
            password=data.get('password'),request_id=request.request_id)
        return Response({'data':result})

class ActivateView(OTPVerifyView):
    purpose=OTPPurpose.ACCOUNT_ACTIVATION
    serializer_class=S.SetPasswordOTP
    action='activate'

class ResetView(OTPVerifyView):
    purpose=OTPPurpose.PASSWORD_RESET
    serializer_class=S.SetPasswordOTP
    action='reset'

class LoginView(AuthAPIView):
    def post(self,request):
        data=validated(S.Login,request)
        throttle(request,'login',data['email'].strip().casefold())
        return token_response(*services.login(data['email'],data['password'],request.request_id))

class RefreshView(AuthAPIView):
    def post(self,request):
        validated(S.EmptyBody,request)
        throttle(request,'refresh')
        return token_response(*services.rotate_refresh(request.COOKIES.get(settings.REFRESH_COOKIE_NAME),request.request_id))

class LogoutView(AuthAPIView):
    def post(self,request):
        validated(S.EmptyBody,request)
        throttle(request,'logout')
        services.logout(request.COOKIES.get(settings.REFRESH_COOKIE_NAME),request.request_id)
        response=Response(status=204)
        response.set_cookie(settings.REFRESH_COOKIE_NAME,'',max_age=0,path=settings.REFRESH_COOKIE_PATH,
            secure=not settings.SILAR_LOCAL_MODE,httponly=True,samesite='Lax')
        return response

class MeView(APIView):
    def get(self,request):
        reject_query(request)
        return Response({'data':S.account_data(request.user)})
    def patch(self,request):
        reject_query(request)
        data=validated(S.ProfilePatch,request)
        with transaction.atomic():
            user=User.objects.select_for_update().get(pk=request.user.pk)
            user.full_name=data['full_name'];user.save(update_fields=['full_name','updated_at'])
            record_event(actor=user,action='PROFILE_UPDATED',object_type='User',object_id=user.id,
                after={'changed_fields':['full_name']},request_id=request.request_id)
        return Response({'data':S.account_data(user)})

class OperatorListView(APIView):
    def get(self,request):
        validate_query(request,[])
        perms=effective_permissions(request.user)
        if request.user.role!=Role.ADMIN or not {'manage_operator','assign_report'}&perms:
            raise ApiProblem('PERMISSION_DENIED','Izin pengelolaan atau penugasan diperlukan.',403)
        target='manage_operator' not in perms
        users=User.objects.filter(role=Role.OPERATOR).order_by('created_at','id')
        if target:
            # Assignment targets may also be ADMIN with explicitly granted Operator rights.
            ids=[u.id for u in User.objects.filter(role__in=[Role.OPERATOR,Role.ADMIN],is_active=True,email_verified_at__isnull=False)
                 if 'view_assigned_report' in effective_permissions(u)]
            users=User.objects.filter(pk__in=ids).order_by('created_at','id')
        from common.api import SilarPagination
        pager=SilarPagination();page=pager.paginate_queryset(users,request)
        return pager.get_paginated_response([S.account_data(u,operator=not target,target=target) for u in page])
    def post(self,request):
        require_admin(request.user,'manage_operator')
        data=validated(S.OperatorCreate,request)
        user=services.create_operator(request.user,data,request.request_id)
        return Response({'data':S.account_data(user,operator=True)},status=201)

class OperatorDetailView(APIView):
    def get(self,request,pk):
        reject_query(request)
        require_admin(request.user,'manage_operator')
        user=User.objects.filter(pk=pk,role=Role.OPERATOR).first()
        if not user:raise Http404
        return Response({'data':S.account_data(user,operator=True)})
    def patch(self,request,pk):
        reject_query(request)
        require_admin(request.user,'manage_operator')
        data=validated(S.OperatorPatch,request)
        user=services.patch_operator(request.user,pk,data,request.request_id)
        return Response({'data':S.account_data(user,operator=True)})

class OperatorPermissionView(APIView):
    def get(self,request):
        require_admin(request.user,'manage_operator');validate_query(request,[])
        from common.api import SilarPagination
        qs=permission_queryset().filter(codename__in=OPERATOR_PERMISSIONS).order_by('id')
        pager=SilarPagination();page=pager.paginate_queryset(qs,request)
        return pager.get_paginated_response([{'id':p.id,'codename':p.codename,'name':p.name} for p in page])

class ActivationDispatchView(APIView):
    def post(self,request,pk):
        reject_query(request)
        require_admin(request.user,'manage_operator');validated(S.EmptyBody,request)
        user=User.objects.filter(pk=pk,role=Role.OPERATOR).first()
        if not user:raise Http404
        services.rate_limit('admin-activation',str(user.pk),limit=settings.OTP_SEND_LIMIT,seconds=settings.OTP_WINDOW_SECONDS)
        otp=services.dispatch_otp(user,OTPPurpose.ACCOUNT_ACTIVATION,actor=request.user,
                                 request_id=request.request_id,admin_dispatch=True)
        return Response({'data':{'operator_id':str(user.id),'challenge_id':str(otp.id),
                                  'expires_at':otp.expires_at,'resend_after':otp.resend_after}},status=202)

