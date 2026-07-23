"""
Django settings for online_learning_system project.
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env file when running locally (ignored on Vercel — env vars are set
# directly in the Vercel dashboard).
# ---------------------------------------------------------------------------
load_dotenv()

AUTH_USER_MODEL = 'users.User'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Better than ['*'] for production
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',           # ← Important for Render
    '.vercel.app',
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',  # ← Add this
    'https://*.vercel.app',
]

# Optional: Add your custom domain if you have one
custom_origin = os.environ.get('CSRF_TRUSTED_ORIGIN')
if custom_origin:
    CSRF_TRUSTED_ORIGINS.append(custom_origin)


# ALLOWED_HOSTS = ['*']

# Allow Vercel domain + any custom domain you add
# CSRF_TRUSTED_ORIGINS = [
#     'https://*.vercel.app',
# ]
custom_origin = os.environ.get('CSRF_TRUSTED_ORIGIN')
if custom_origin:
    CSRF_TRUSTED_ORIGINS.append(custom_origin)
# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'category',
    'lessons',
    'assignments',
    'submissions',
    'reviews',
    'enrollments',
    'employees',
    'courses',
    'students',
    'instructors',
    'users',
    'dashboard',
    'adminpanel',
    'quizzes',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'adminpanel.middleware.CurrentUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'online_learning_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.debug",
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notifications_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'online_learning_system.wsgi.application'

# ---------------------------------------------------------------------------
# Database
# If DATABASE_URL env var is set (Vercel / Neon) → use PostgreSQL.
# Otherwise → use local SQLite3 for development.
# ---------------------------------------------------------------------------
_database_url = os.environ.get('DATABASE_URL')

if _database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ---------------------------------------------------------------------------
# Static files  (WhiteNoise serves these on Vercel)
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# Replace your current STATICFILES_STORAGE line with this:
if DEBUG:
    # Use standard storage for local development so updates show instantly
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    # Use optimized WhiteNoise compression only on Vercel production
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ---------------------------------------------------------------------------
# Media files
# If Cloudinary credentials are present (production) → use Cloudinary storage.
# Otherwise → store files locally in /media/ (development).
# ---------------------------------------------------------------------------
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    import cloudinary
    # ត្រូវប្រាកដថាបានដំឡើង django-cloudinary-storage ក្នុង requirements.txt
    import cloudinary_storage 

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )

    # បញ្ចូល App ទាំងពីរទៅទីតាំងខាងលើគេបង្អស់នៃ INSTALLED_APPS
    INSTALLED_APPS.insert(0, 'cloudinary_storage')
    INSTALLED_APPS.insert(1, 'cloudinary')
    
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = f'https://cloudinary.com{CLOUDINARY_CLOUD_NAME}/'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = 'dashboard_redirect'
LOGOUT_REDIRECT_URL = "home"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@inventory.example"