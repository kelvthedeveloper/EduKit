import os
from .base import *

DEBUG = False

DEPLOYMENT_MODE = 'school-server'

_extra_hosts = [
    'localhost', '127.0.0.1', 'school.local', '*.local',
    '192.168.0.0/16', '10.0.0.0/8', '172.16.0.0/12',
]
ALLOWED_HOSTS = _extra_hosts + [
    h for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://school.local',
]
_extra_cors = os.environ.get('SCHOOL_SERVER_LAN_HOSTNAMES', '')
if _extra_cors:
    CORS_ALLOWED_ORIGINS += [f'http://{h}' for h in _extra_cors.split(',') if h]
    CORS_ALLOWED_ORIGINS += [f'https://{h}' for h in _extra_cors.split(',') if h]

CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)

_school_https = os.environ.get('SCHOOL_SERVER_HTTPS', '').lower() in ('1', 'true', 'yes', 'on')
SESSION_COOKIE_SECURE = _school_https
CSRF_COOKIE_SECURE = _school_https
if _school_https:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SESSION_COOKIE_AGE = 60 * 60 * 12  # 12 hours on school server
SESSION_COOKIE_DOMAIN = None  # Let Django infer; LAN subdomains handled by Nginx

SYNC_MODE = 'school_server'
LOCAL_CACHE_ENABLED = True

CACHES['default']['TIMEOUT'] = 600

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
