import os
import sys
from setuptools import find_packages, setup
sys.path.insert(0, 'django_find')
from version import __version__

descr = '''
django-find is a Django app that makes it easy to add complex
search functionality to your project. It supports two different ways
to search your Django models: Query-based, or JSON-based.

By query-based, we mean that you can use statements like these
to search (filter) your model:

- `hello world`
- `author:"robert frost" and (title:road or chapter:2)`

You can also create complex multi-model searches/filters by
using a JSON-based query.

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
    description='Simple but powerful search/filter functionality to Django projects',
    long_description=descr,
    url='https://github.com/knipknap/django-find',
    author='Samuel Abels',
    author_email='knipknap@gmail.com',
    install_requires=['future',
                      'Django>=1.11,<2',
                      'mysqlclient',
                      'dateparser']
    keywords=' '.join(['django',
                       'search',
                       'find',
                       'filter',
                       'query',
                       'json',
                       'sql',
                       'app']),
    classifiers=[
        'Environment :: Web Environment',
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Text Processing :: Filters',
    ],
)
