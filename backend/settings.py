from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'یک_کلید_امنیتی_قوی_و_تصادفی'

# ⚠️ برای Render و محیط واقعی
DEBUG = True
ALLOWED_HOSTS = ['django-rz65.onrender.com', 'localhost','127.0.0.1']

# --- اپ‌ها ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',
    'api',  # اپ شما
]

# --- میدلورها ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF فعال
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# --- دیتابیس PostgreSQL Render (External) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'froshgah_ehhr',
        'USER': 'froshgah_ehhr_user',
        'PASSWORD': 'aR1XsnBsrumhYjCSohaJmTVJCTR1zhav',
        'HOST': 'dpg-d3t10todl3ps73b0mt90-a.singapore-postgres.render.com',
        'PORT': '5432',
    }
}

# --- پسوردها ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- زبان و زمان ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# --- استاتیک و مدیا ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CORS ---
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # فرانت لوکال
    'https://shop-site.example.com',  # دامنه فرانت اصلی
]
CORS_ALLOW_CREDENTIALS = True  # اجازه ارسال کوکی با درخواست‌ها

# --- Rest Framework ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',  # Session به جای JWT
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',  # اجازه دسترسی فقط به کاربران وارد شده
    ),
}

# --- تنظیم ایمیل ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'abtin.amraei@gmail.com'
EMAIL_HOST_PASSWORD = 'pnjn mcbt tpps zlmc'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# --- CSRF ---
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_HTTPONLY = False  # JS می‌تونه کوکی بخونه (برای fetch)
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'https://shop-site.example.com',
]

# --- SESSION ---
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # اگر روی HTTPS واقعی: True
SESSION_COOKIE_SAMESITE = 'Lax'  # جلوگیری از CSRF Cross-site
