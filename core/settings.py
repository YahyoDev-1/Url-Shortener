"""
Django settings for core project (Advanced URL Shortener).

Maxfiy sozlamalar .env faylidan o'qiladi (python-dotenv orqali).
Ma'lumotlar bazasi: MongoDB (django-mongodb-backend orqali).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# .env faylini yuklash
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY topilmadi! .env faylini tekshiring (.env.example ga qarang).')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# HTTPS domenlar uchun (masalan: https://loyiha.up.railway.app)
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]

# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'mongo_apps.MongoAdminConfig',       # django.contrib.admin (MongoDB uchun)
    'mongo_apps.MongoAuthConfig',        # django.contrib.auth (MongoDB uchun)
    'mongo_apps.MongoContentTypesConfig',  # django.contrib.contenttypes (MongoDB uchun)
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'accounts',
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Statik fayllar (production)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database — MongoDB (django-mongodb-backend)
# https://www.mongodb.com/docs/languages/python/django-mongodb/

DATABASES = {
    'default': {
        'ENGINE': 'django_mongodb_backend',
        'NAME': os.getenv('MONGODB_NAME', 'url_shortener_db'),
        'HOST': os.getenv('MONGODB_URI', 'mongodb://localhost:27017'),
    },
}

# MongoDB uchun contrib ilovalarning migratsiyalari ObjectId'ga moslashtiriladi
MIGRATION_MODULES = {
    'admin': 'mongo_migrations.admin',
    'auth': 'mongo_migrations.auth',
    'contenttypes': 'mongo_migrations.contenttypes',
}

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Autentifikatsiya yo'nalishlari
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'main:home'

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [BASE_DIR / 'static']

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

if not DEBUG:
    # WhiteNoise: statik fayllarni siqib (gzip/brotli) xizmat qiladi
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
    }

# MongoDB'da asosiy kalit ObjectId bo'ladi
DEFAULT_AUTO_FIELD = 'django_mongodb_backend.fields.ObjectIdAutoField'

# ============================================================
# Production xavfsizlik sozlamalari (DEBUG=False bo'lganda)
# ============================================================
if not DEBUG:
    # Railway (va boshqa PaaS) reverse-proxy ortida HTTPS'ni shu header orqali bildiradi
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 kun
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
