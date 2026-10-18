from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CurrentUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user=super().get_user(validated_token)
        if not user.is_active or not user.email_verified_at or validated_token.get('auth_version')!=user.auth_version:
            raise AuthenticationFailed('Sesi tidak dapat digunakan.')
        return user

class VerifiedAccount(BasePermission):
    message='Akun aktif dan terverifikasi diperlukan.'
    def has_permission(self, request, view):
        u=request.user
        return bool(u and u.is_authenticated and u.is_active and u.email_verified_at)

