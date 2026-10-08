import os
from .base import *

DEBUG = False

_allowed = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h for h in _allowed.split(',') if h] if _allowed else []

_cors = os.environ.get('DJANGO_CORS_ORIGIN_WHITELIST', '')
CORS_ALLOWED_ORIGINS = [h for h in _cors.split(',') if h] if _cors else []

_csrf = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [h for h in _csrf.split(',') if h] if _csrf else []

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)

CACHES['default']['TIMEOUT'] = 600

LOGGING['handlers']['file'] = {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': os.environ.get('LOG_FILE', '/var/log/edukit/app.log'),
    'maxBytes': 10 * 1024 * 1024,
    'backupCount': 5,
    'formatter': 'verbose',
}
for logger in LOGGING['loggers'].values():
    logger.setdefault('handlers', []).append('file')
