# settings.py

import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # برای تولید باید False شود

ALLOWED_HOSTS = ['*']  # بهتره دامنه یا آی‌پی سرورت رو اینجا بزنی

# Application definition
INSTALLED_APPS = [
    # اپ‌های پیش‌فرض جنگو
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # اپ‌های خودت
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR := os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'templates'],
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


# تنظیمات دیتابیس MySQL روی InfinityFree
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'if0_39669148_froshgah',  # نام دیتابیس
        'USER': 'if0_39669148',            # یوزرنیم دیتابیس
        'PASSWORD': 'rwhGqygmSi',          # پسورد دیتابیس
        'HOST': 'sql111.infinityfree.com', # هاست دیتابیس
        'PORT': '3306',                    # پورت دیتابیس
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
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


# بین‌المللی‌سازی
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# مسیر فایل‌های استاتیک
STATIC_URL = '/static/'

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# رسانه (مدیا)
MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# پیش‌فرض ID فیلدها در مدل‌ها (از Django 3.2 به بعد)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
