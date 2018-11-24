.. image:: _static/logo.png
    :target: http://django-find.readthedocs.io

|

.. image:: https://travis-ci.org/knipknap/django-find.svg?branch=master
    :target: https://travis-ci.org/knipknap/django-find

.. image:: https://coveralls.io/repos/github/knipknap/django-find/badge.svg?branch=master
    :target: https://coveralls.io/github/knipknap/django-find?branch=master

.. image:: https://lima.codeclimate.com/github/knipknap/django-find/badges/gpa.svg
    :target: https://lima.codeclimate.com/github/knipknap/django-find
    :alt: Code Climate

.. image:: https://img.shields.io/github/stars/knipknap/django-find.svg
    :target: https://github.com/knipknap/django-find/stargazers

.. image:: https://img.shields.io/github/license/knipknap/django-find.svg
    :target: https://github.com/knipknap/django-find/blob/master/COPYING

django-find
===========

What is django-find?
--------------------

**django-find** is a Django app that makes it easy to add complex
search functionality for the models in your project.

**django-find** supports two different ways to search your Django models:
Query-based, or JSON-based.

By query-based, we mean that you can use statements like these
to search your model::

        author:"robert frost" and (title:road or chapter:2)

To make it easy to do complex searches spanning multiple models, another
method is provided. For example, you may want to allow for custom searches
that let the user choose which models and columns to include.
In other words, a user interface like this:

.. image:: _static/custom.png
    :alt: Custom Search

For this, a JSON-based search functionality is provided::

        {
            "Author":{"name":[[["equals","test"]]]},
            "Book": {"title":[[["notcontains","c"]]]},
            "Chapter": {"content":[[["startswith","The "]]]}
        }

django-find is smart in figuring out how to join those models
together and return a useful result.

django-find also provides a template tag that you can use to
render a search field::

    {% load find_tags %}
    {% find object_list %}
    {% for obj in object_list %}
        {{ obj.name }}
    {% endfor %}

What isn't django-find?
=======================

**django-find** is not a full text search engine, it searches the fields
of your models. In other words, it searches and provides tabular data.

Contents
--------

.. toctree::
   :maxdepth: 2

   install
   tutorial
   query
   API Documentation<modules>

Development
-----------

django-find is on `GitHub <https://github.com/knipknap/django-find>`_.

License
-------
django-find is published under the `MIT licence <https://opensource.org/licenses/MIT>`_.
