# multifunction_platform/settings.py
import os
from pathlib import Path
from django.contrib.messages import constants as message_constants
from decouple import config

import logging

# Configurer les logs pour ne pas afficher les informations sensibles
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

DEBUG = True

print("EMAIL_HOST_USER:", EMAIL_HOST_USER)
print("EMAIL_HOST_PASSWORD:", EMAIL_HOST_PASSWORD)

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users.apps.UsersConfig',
    'ecommerce',
    'blog',
    'orders',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'django_ckeditor_5',
    'axes',
    'widget_tweaks',
    
    # 'channels' a été retiré
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'multifunction_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                'ecommerce.context_processors.cart_count',  # Ajoute ceci
            ],
        },
    },
]

WSGI_APPLICATION = 'multifunction_platform.wsgi.application'
# ASGI_APPLICATION a été retiré car nous n'utilisons plus channels

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

if DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

CSRF_COOKIE_ROTATE = False

AXES_FAILURE_LIMIT = 20
AXES_COOLOFF_TIME = 1
AXES_RESET_ON_SUCCESS = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'axes': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'axes-cache',
    }
}
AXES_CACHE = 'axes'
LOGIN_URL = 'users:login'

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

X_FRAME_OPTIONS = 'DENY'

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'

CKEDITOR_5_CONFIGS = {
    'default': {
        "toolbar": [
            "heading", "|", "bold", "italic", "underline", "|",
            "link", "blockQuote", "imageUpload", "|", "undo", "redo"
        ],
        "image": {
            "toolbar": [
                "imageTextAlternative", "|",
                "imageStyle:alignLeft", "imageStyle:full",
                "imageStyle:alignRight"
            ],
        },
    }
}

MESSAGE_TAGS = {
    message_constants.DEBUG: 'alert-info',
    message_constants.INFO: 'alert-info',
    message_constants.SUCCESS: 'alert-success',
    message_constants.WARNING: 'alert-warning',
    message_constants.ERROR: 'alert-danger',
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER')

SESSION_COOKIE_AGE = 1209600
SESSION_SAVE_EVERY_REQUEST = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'axes_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/axes.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'axes': {
            'handlers': ['axes_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}