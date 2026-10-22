"""Supplementary API tests only. Does not validate PostgreSQL triggers/locks."""
import os
if os.getenv('SILAR_ALLOW_COMPONENT_DB') != '1':
    raise RuntimeError('SQLite hanya untuk tes komponen eksplisit; gunakan PostgreSQL 16 untuk aplikasi.')
from config.test_settings import *  # noqa: F403
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
MIGRATION_MODULES = {'core': None, 'accounts': None}
