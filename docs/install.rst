Installation
============

Prerequisites
-------------

django-find requires Python 2.7 or Python 3.5 or greater, and the following modules:

.. literalinclude:: ../requirements.txt

Getting started
---------------

Download and install the module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download and install using PIP::

    sudo pip3 install django-find

Alternatively, you may also install the latest development version
from GitHub::

    git clone git://github.com/knipknap/django-find
    cd django-find
    sudo make install

Add it to your Django project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add "django_find" to your ``INSTALLED_APPS`` setting like this::

    INSTALLED_APPS = [
        ...
        'django_find',
    ]

Add it to your models
~~~~~~~~~~~~~~~~~~~~~

You are now ready to start using the Searchable decorator.
For more information, please continue with the
:doc:`tutorial <tutorial>`.

Running the automated test suite
--------------------------------

If you installed from GitHub, you can run the integrated test suite::

    make tests

There shouldn't be any errors, so if something comes up,
`please file a bug <https://github.com/knipknap/django-find/issues>`_.
