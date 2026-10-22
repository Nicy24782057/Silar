from django.urls import path
from accounts import views as a
from core.views import health,AuditListView

urlpatterns=[
    path('health/',health,name='health'),
    path('api/v1/auth/csrf/',a.CSRFView.as_view()),
    path('api/v1/auth/register/',a.RegisterView.as_view()),
    path('api/v1/auth/otp/request/',a.OTPRequestView.as_view()),
    path('api/v1/auth/otp/verify/',a.OTPVerifyView.as_view()),
    path('api/v1/auth/operators/activate/',a.ActivateView.as_view()),
    path('api/v1/auth/password/reset/',a.ResetView.as_view()),
    path('api/v1/auth/login/',a.LoginView.as_view()),
    path('api/v1/auth/refresh/',a.RefreshView.as_view()),
    path('api/v1/auth/logout/',a.LogoutView.as_view()),
    path('api/v1/me/',a.MeView.as_view()),
    path('api/v1/admin/operators/',a.OperatorListView.as_view()),
    path('api/v1/admin/operator-permissions/',a.OperatorPermissionView.as_view()),
    path('api/v1/admin/operators/<uuid:pk>/',a.OperatorDetailView.as_view()),
    path('api/v1/admin/operators/<uuid:pk>/activation-otp/',a.ActivationDispatchView.as_view()),
    path('api/v1/admin/audit/',AuditListView.as_view()),
]
handler404='common.api.not_found'
handler500='common.api.server_error'

# SLR_10 input endpoints
from django.urls import include
urlpatterns += [path('api/v1/', include('reporting.urls'))]
