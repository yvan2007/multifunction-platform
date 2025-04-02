# settings.py
import os
from pathlib import Path
from django.contrib.messages import constants as message_constants  # Changé de 'messages' à 'message_constants'
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Charger les variables depuis le fichier .env
SECRET_KEY = config('SECRET_KEY')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

DEBUG = True

print("EMAIL_HOST_USER:", EMAIL_HOST_USER)
print("EMAIL_HOST_PASSWORD:", EMAIL_HOST_PASSWORD)

MESSAGE_TAGS = {
    message_constants.DEBUG: 'alert-info',
    message_constants.INFO: 'alert-info',
    message_constants.SUCCESS: 'alert-success',
    message_constants.WARNING: 'alert-warning',
    message_constants.ERROR: 'alert-danger',
}

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'multifunction_platform',
    'users',
    'ecommerce',
    'blog',
    'orders',
    'rest_framework',
    'drf_yasg',
    'django_ckeditor_5',
    'axes',
    'widget_tweaks',
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
                'multifunction_platform.context_processors.cart_item_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'multifunction_platform.wsgi.application'

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

# Désactiver HTTPS en développement
if DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS (en production uniquement)
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Désactiver la rotation du jeton CSRF en développement (pour tester)
CSRF_COOKIE_ROTATE = False

# Configuration de django-axes
AXES_FAILURE_LIMIT = 20  # Verrouillage après 5 tentatives échouées
AXES_COOLOFF_TIME = 1  # Verrouillage pendant 1 heure
AXES_RESET_ON_SUCCESS = True

# Cache pour django-axes
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

# Sécurité des sessions
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Protection contre le clickjacking
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

# Configuration CKEditor 5
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
        "upload_url": "/ckeditor5/upload/",
    }
}

CKEDITOR_UPLOAD_PATH = "uploads/"

# Messages Bootstrap
MESSAGE_TAGS = {
    message_constants.DEBUG: 'alert-info',
    message_constants.INFO: 'alert-info',
    message_constants.SUCCESS: 'alert-success',
    message_constants.WARNING: 'alert-warning',
    message_constants.ERROR: 'alert-danger',
}

# Configuration Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# EMAIL_HOST_USER et EMAIL_HOST_PASSWORD sont maintenant lus depuis .env
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER')

# Session Configuration for Cart
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_SAVE_EVERY_REQUEST = True

# Configuration de la journalisation pour django-axes
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
    },
}