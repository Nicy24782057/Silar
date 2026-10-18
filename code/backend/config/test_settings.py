from .settings import *  # noqa: F403

DEBUG = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
# Fast hasher is isolated to the test runner; production uses Django defaults.
