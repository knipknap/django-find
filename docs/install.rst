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

Make sure that the request object is available to templates!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you haven't already, you should also install Django's
`django.template.context_processors.request <https://docs.djangoproject.com/en/2.1/ref/templates/api/#django-template-context-processors-request>`_
and
`django.template.context_processors.i18n <https://docs.djangoproject.com/en/2.1/ref/templates/api/#django-template-context-processors-i18n>`_.

In other words, your settings need to set the TEMPLATES
variable to include the context_processors like so::

	TEMPLATES = [
	    {
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [
		    # ...
		],
		'APP_DIRS': True,
		'OPTIONS': {
		    'context_processors': [
			# ...
			'django.template.context_processors.i18n',
			'django.template.context_processors.request',
		    ],
		},
	    },
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
