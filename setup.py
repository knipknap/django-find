import os
import sys
from setuptools import find_packages, setup
sys.path.insert(0, 'django_find')
from version import __version__

descr = '''
django-find is a Django app that makes it easy to add complex
search functionality to your project. It supports two different ways
to search your Django models: Query-based, or JSON-based.

Checkout the README.md on Github for more information.
'''.strip()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-find',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='Easily add complex search functionality to Django projects',
    long_description=descr,
    url='https://github.com/knipknap/django-find',
    author='Samuel Abels',
    author_email='knipknap@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
