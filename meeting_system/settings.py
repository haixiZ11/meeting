import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-meeting-system-secret-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'simpleui',  # SimpleUI必须放在django.contrib.admin之前
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'booking',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 添加WhiteNoise中间件处理静态文件
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meeting_system.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'meeting_system.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'data', 'db.sqlite3')),
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

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# WhiteNoise配置
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# SimpleUI配置
SIMPLEUI_DEFAULT_THEME = 'admin.lte.css'
SIMPLEUI_DESIGN = 'https://element.eleme.io'
SIMPLEUI_HOME_INFO = False
SIMPLEUI_ANALYSIS = False
SIMPLEUI_STATIC_OFFLINE = True
SIMPLEUI_HOME_TITLE = 'Etek会议室预约系统管理'
SIMPLEUI_HOME_ICON = 'fas fa-calendar-alt'
SIMPLEUI_LOGO = 'https://avatars2.githubusercontent.com/u/13655483?s=60&v=4'

# 自定义管理界面配置
SIMPLEUI_CONFIG = {
    'system_keep': False,
    'menu_display': ['会议室预约系统', '认证和授权'],
    'dynamic': True,
    'menus': [
        {
            'name': '会议室管理',
            'icon': 'fas fa-door-open',
            'models': [
                {
                    'name': '会议室',
                    'icon': 'fas fa-door-open',
                    'url': '/admin/booking/room/'
                },
                {
                    'name': '预约记录',
                    'icon': 'fas fa-calendar-check',
                    'url': '/admin/booking/reservation/'
                },
                {
                    'name': '系统设置',
                    'icon': 'fas fa-cog',
                    'url': '/admin/booking/systemsetting/'
                }
            ]
        },
        {
            'name': '用户管理',
            'icon': 'fas fa-users',
            'models': [
                {
                    'name': '用户',
                    'icon': 'fas fa-user',
                    'url': '/admin/auth/user/'
                },
                {
                    'name': '用户组',
                    'icon': 'fas fa-users-cog',
                    'url': '/admin/auth/group/'
                }
            ]
        }
    ]
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
