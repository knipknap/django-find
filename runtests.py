#!/usr/bin/env python2
import glob
import os
import sys

import django
from django.conf import settings
from django.core.management import execute_from_command_line


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))

# Unfortunately, apps can not be installed via ``modify_settings``
# decorator, because it would miss the database setup.
CUSTOM_INSTALLED_APPS = (
    'django_find',
    'tests',
    'django.contrib.admin',
)

ALWAYS_INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

ALWAYS_MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.messages.context_processors.messages',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
            ],
        },
    },
]

settings.configure(
    SECRET_KEY="django_tests_secret_key",
    DEBUG=False,
    TEMPLATE_DEBUG=False,
    ALLOWED_HOSTS=[],
    INSTALLED_APPS=ALWAYS_INSTALLED_APPS + CUSTOM_INSTALLED_APPS,
    MIDDLEWARE=ALWAYS_MIDDLEWARE_CLASSES,
    TEMPLATES=TEMPLATES,
    ROOT_URLCONF='tests.urls',
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    LANGUAGE_CODE='en-us',
    TIME_ZONE='UTC',
    USE_I18N=True,
    USE_L10N=True,
    USE_TZ=True,
    STATIC_URL='/static/',
    # Use a fast hasher to speed up tests.
    PASSWORD_HASHERS=(
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ),
    FIXTURE_DIRS=glob.glob(BASE_DIR + '/' + '*/fixtures/')

)

django.setup()
args = [sys.argv[0], 'test']
# Current module (``tests``) and its submodules.
test_cases = '.'

# Allow accessing test options from the command line.
offset = 1
try:
    sys.argv[1]
except IndexError:
    pass
else:
    option = sys.argv[1].startswith('-')
    if not option:
        test_cases = sys.argv[1]
        offset = 2

args.append(test_cases)
# ``verbosity`` can be overwritten from command line.
args.append('--verbosity=2')
args.extend(sys.argv[offset:])

execute_from_command_line(args)
