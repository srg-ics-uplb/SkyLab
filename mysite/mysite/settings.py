"""
Django settings for mysite project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '34%6w9p0c(kmpgzuaqrl4fbc%=*b_!y63eoihloqjz$uh*v8&y'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []
# ALLOWED_HOSTS = ['127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'django_ajax',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'crispy_forms',
    'skylab',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'mysite.urls'

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

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

SOCIALACCOUNT_PROVIDERS = \
    {'google':
         {'SCOPE': ['profile', 'email'],
          'AUTH_PARAMS': {'access_type': 'online'}}}


WSGI_APPLICATION = 'mysite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases


# For final deployment

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'skylab',
#         'USER': 'root',
#         'PASSWORD': 'pass',
#         'HOST': 'localhost',
#         'PORT': '',
#     }
# }

#For development only
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}



# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

#crispy form settings
CRISPY_TEMPLATE_PACK = 'bootstrap4'

#email server settings
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

#displays email in console instead of sending it
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

PRIVATE_MEDIA_ROOT = MEDIA_ROOT
PRIVATE_MEDIA_URL = MEDIA_URL

SENDFILE_ROOT = MEDIA_ROOT

SENDFILE_URL = '/media'

# SENDFILE_BACKEND = 'sendfile.backends.mod_wsgi'
SENDFILE_BACKEND = 'sendfile.backends.xsendfile'

SKYLAB_MODULES_PACKAGE = "skylab.modules"  # : skylab/modules
MAX_NODES_PER_CLUSTER = 5
MAX_TOTAL_INSTANCES = 25  # current limit of vcluster : 32

FRONTEND_IP = "10.0.3.101"
FRONTEND_USERNAME = "user"
FRONTEND_PASSWORD = "excellence"

CLUSTER_USERNAME = "mpiuser"
CLUSTER_PASSWORD = "mpiuser"

CLUSTER_PASSWORD = "mpiuser"

SITE_ID = 1
SOCIALACCOUNT_ADAPTER = "skylab.googleadapter.UniversityAccountAdapter"
SOCIALACCOUNT_QUERY_EMAIL = True
LOGIN_URL = '/skylab/accounts/google/login/?process=login'
LOGIN_REDIRECT_URL = '/skylab'

JSMOL_SERVER_URL = "http://webserver.localhost.com/jsmol/php/jsmol.php"

TRY_WHILE_NOT_EXIT_MAX_TIME = 300  # in seconds, max wait time for try while not exit loops in project
