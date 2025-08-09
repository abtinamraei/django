from pathlib import Path

# مسیر پایه پروژه
BASE_DIR = Path(__file__).resolve().parent.parent

# =======================
# تنظیمات اصلی
# =======================
SECRET_KEY = 'یک_کلید_امنیتی_قوی_و_تصادفی'
DEBUG = True
ALLOWED_HOSTS = ['*']  # برای تولید بهتر دامنه‌ها را دقیق مشخص کن

# =======================
# اپلیکیشن‌های نصب شده
# =======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',  # حتما نصب باشه: pip install django-cors-headers
    'api',
]

# =======================
# Middleware ها
# =======================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # حتما قبل از CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =======================
# روت urls.py
# =======================
ROOT_URLCONF = 'backend.urls'

# =======================
# Template Settings
# =======================
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

# =======================
# WSGI Application
# =======================
WSGI_APPLICATION = 'backend.wsgi.application'

# =======================
# تنظیمات دیتابیس PostgreSQL
# =======================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'froshgahaaw_db',
        'USER': 'postgres',
        'PASSWORD': 'mF2SUpL!paap8PMq4eDd',
        'HOST': 'remote-fanhab.runflare.com',
        'PORT': '31217',
    }
}

# =======================
# Password validation
# =======================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =======================
# تنظیمات زبان و منطقه زمانی
# =======================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# =======================
# Static files
# =======================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =======================
# کلید پیش‌فرض
# =======================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =======================
# تنظیمات CORS (برای دسترسی فرانت به بک‌اند)
# =======================
CORS_ALLOW_ALL_ORIGINS = True  # فقط برای تست؛ در تولید محدودش کن
