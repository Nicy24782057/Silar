from datetime import timedelta
from pathlib import Path
import os
from urllib.parse import urlparse
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=False)

def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ('1', 'true', 'yes')

def env_list(name, default=''):
    return [x.strip() for x in os.getenv(name, default).split(',') if x.strip()]

def required_secret(name):
    value = os.getenv(name, '')
    if len(value) < 32 or value == 'CHANGE_ME':
        raise ImproperlyConfigured(f'{name} harus berisi rahasia acak minimal 32 karakter.')
    return value

SILAR_LOCAL_MODE = env_bool('SILAR_LOCAL_MODE')
DEBUG = env_bool('DEBUG') and SILAR_LOCAL_MODE
SECRET_KEY = required_secret('SECRET_KEY')
JWT_SIGNING_KEY = required_secret('JWT_SIGNING_KEY')
OTP_HMAC_KEY = required_secret('OTP_HMAC_KEY')
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://localhost').rstrip('/')
if not FRONTEND_URL.startswith('https://'):
    parsed = urlparse(FRONTEND_URL)
    if not (SILAR_LOCAL_MODE and parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1')):
        raise ImproperlyConfigured('FRONTEND_URL memerlukan HTTPS; HTTP hanya untuk localhost pada SILAR_LOCAL_MODE.')
FRONTEND_VERIFY_PATH = os.getenv('FRONTEND_VERIFY_PATH', '/verify-email')
FRONTEND_ACTIVATE_PATH = os.getenv('FRONTEND_ACTIVATE_PATH', '/activate-operator')
FRONTEND_RESET_PATH = os.getenv('FRONTEND_RESET_PATH', '/reset-password')
for p in (FRONTEND_VERIFY_PATH, FRONTEND_ACTIVATE_PATH, FRONTEND_RESET_PATH):
    if not p.startswith('/') or p.startswith('//') or '?' in p or '#' in p:
        raise ImproperlyConfigured('Path halaman akun harus path lokal tanpa query atau fragment.')

INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
    'rest_framework', 'rest_framework_simplejwt.token_blacklist', 'corsheaders',
    'accounts', 'core',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'common.middleware.RequestMetadataMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv('DB_NAME', 'silar_local'), 'USER': os.getenv('DB_USER', 'silar_app'),
    'PASSWORD': os.getenv('DB_PASSWORD', ''), 'HOST': os.getenv('DB_HOST', '127.0.0.1'),
    'PORT': os.getenv('DB_PORT', '5432'), 'CONN_MAX_AGE': 0,
    'OPTIONS': {'connect_timeout': 8},
}}
AUTH_USER_MODEL = 'accounts.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
     'OPTIONS': {'user_attributes': ('email', 'full_name')}},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['accounts.authentication.CurrentUserJWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['accounts.authentication.VerifiedAccount'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'EXCEPTION_HANDLER': 'common.api.exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'common.api.SilarPagination', 'PAGE_SIZE': 20,
    'UNAUTHENTICATED_USER': None,
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('ACCESS_TOKEN_MINUTES', '15'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('REFRESH_TOKEN_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': True, 'BLACKLIST_AFTER_ROTATION': True,
    'SIGNING_KEY': JWT_SIGNING_KEY, 'USER_ID_FIELD': 'id', 'USER_ID_CLAIM': 'user_id',
    'UPDATE_LAST_LOGIN': False,
}
REFRESH_COOKIE_NAME = 'silar_refresh'
REFRESH_COOKIE_PATH = '/api/v1/auth/'
SESSION_COOKIE_SECURE = not SILAR_LOCAL_MODE
CSRF_COOKIE_SECURE = not SILAR_LOCAL_MODE
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', FRONTEND_URL)
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS', FRONTEND_URL)
CORS_ALLOW_CREDENTIALS = True
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = (*default_headers, 'idempotency-key')
CORS_EXPOSE_HEADERS = ['Idempotency-Replayed', 'Retry-After', 'X-Request-ID']
SECURE_SSL_REDIRECT = not SILAR_LOCAL_MODE
SECURE_HSTS_SECONDS = 0 if SILAR_LOCAL_MODE else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not SILAR_LOCAL_MODE
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
PRIVATE_MEDIA_ROOT = BASE_DIR / 'private_media'
MODEL_ASSET_ROOT = BASE_DIR / 'model_assets'
EMAIL_FILE_PATH = BASE_DIR / 'private_outbox'
EMAIL_MODE = os.getenv('EMAIL_MODE', 'smtp')
if EMAIL_MODE == 'file' and not SILAR_LOCAL_MODE:
    raise ImproperlyConfigured('Email file hanya diizinkan pada mode lokal.')
EMAIL_BACKEND = ('common.email_backend.PrivateFileEmailBackend' if EMAIL_MODE == 'file'
                 else 'django.core.mail.backends.smtp.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'SILAR <noreply@localhost>')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_TIMEOUT = 10
OTP_TTL_SECONDS = int(os.getenv('OTP_TTL_SECONDS', '600'))
OTP_RESEND_SECONDS = int(os.getenv('OTP_RESEND_SECONDS', '60'))
OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', '5'))
OTP_SEND_LIMIT = int(os.getenv('OTP_SEND_LIMIT', '5'))
OTP_WINDOW_SECONDS = int(os.getenv('OTP_WINDOW_SECONDS', '900'))
ANALYSIS_CAPACITY = int(os.getenv('ANALYSIS_CAPACITY', '1'))
if EMAIL_MODE not in ('file','smtp'):
    raise ImproperlyConfigured('EMAIL_MODE harus file atau smtp.')
for value in (OTP_TTL_SECONDS,OTP_RESEND_SECONDS,OTP_MAX_ATTEMPTS,OTP_SEND_LIMIT,OTP_WINDOW_SECONDS,ANALYSIS_CAPACITY):
    if value<1:raise ImproperlyConfigured('Batas OTP dan kapasitas harus bilangan positif.')
IDEMPOTENCY_TTL_SECONDS = 86400
LANGUAGE_CODE = 'id'
TIME_ZONE = 'UTC'
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 27 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
APPEND_SLASH = True

# SLR_10 input service
if 'reporting' not in INSTALLED_APPS:
    INSTALLED_APPS += ['reporting']
