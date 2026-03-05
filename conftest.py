import django
from django.conf import settings


def pytest_configure():
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    django.setup()
