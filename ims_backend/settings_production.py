"""
Production settings for IMS Backend
"""

from .settings import *
import os
from decouple import config
import dj_database_url

# Override settings for production
DEBUG = config('DEBUG', default=False, cast=bool)

# Security settings
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    ALLOWED_HOSTS = ['*']  # Fallback, but should be configured properly

# Database configuration for production
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3')
    )
}

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CORS settings
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@ims.com')

# Redis configuration
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')

# Django-Q configuration for production
Q_CLUSTER = {
    'name': 'ims_backend',
    'workers': config('Q_WORKERS', default=2, cast=int),
    'recycle': 500,
    'timeout': 60,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'redis': REDIS_URL
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'notifications': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Disable problematic apps for production deployment
# Ensure 'purchasing' is enabled in production so /api/purchasing/* endpoints work
LOCAL_APPS = [
    'accounts',
    'inventory',
    'supermarkets',
    'notifications',
    'purchasing',  # enable purchasing app in production
    # Temporarily disable apps with heavy dependencies
    # 'pos_integration',
    # 'file_processing',
    # 'analytics',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS