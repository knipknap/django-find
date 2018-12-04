Tutorial
========

Introduction
------------

We'll assume that django-find is already installed, and added
to your Django project. The instructions are :doc:`here <install>`.

Motivation
----------

Assume you want to add a search box to your user interface, where
your users can search your models using a simple query language.
For example:

- ``hello world`` (searches all fields for hello and world)
- ``robert OR title:road`` (searches all fields for "robert", and "title" for "road")

The documentation of the query language is :doc:`here <query>`.

Alternatively, you may want to allow the user to specify the
models and columns to display with a UI like this:

.. image:: _static/custom.png
    :target: http://django-find.readthedocs.io

django-find supports JSON-based queries for this purpose.

Getting started
---------------

Enabling the functionality is as simple as adding the "Searchable"
mixin to your models. Example::

        from django.db import models
        from django_find import Searchable

        class Author(models.Model, Searchable):
            name = models.CharField("Author Name", max_length=10)

        class Book(models.Model, Searchable):
            author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Author')
            title = models.CharField("Title", max_length=80)
            rating = models.IntegerField("Rating")
            internal_id = models.CharField(max_length=10)

That is all, you are now ready to query your models using your own code,
or in your templates.

Query from your own code
------------------------

All models having the Searchable mixin added provide the following methods::

        # Query-based search returns a standard Django QuerySet that you
        # can .filter() and work with as usual.
        query = Book.by_query('author:"robert frost" and title:"the road"')

        # You can also get a Django Q object for the statements.
        q_obj = Book.q_from_query('author:"robert frost" and title:"the road"')

        # JSON-based search exhausts what Django's ORM can do, so it does
        # not return a Django QuerySet, but a row-based PaginatedRawQuerySet:
        query, field_list = Book.by_json_raw('''{
            "Chapter": {"title":[[["contains","foo"]]]}
        }''')
        print('|'.join(field_list))
        for row in query:
            print('|'.join(row))

You can pass the PaginatedRawQuerySet to Django templates as you
would with a Django QuerySet, as it supports slicing and
pagination.

In most cases, you also want to specify some other, related
fields that can be searched, or exclude some columns from the search.
The following example shows how to do that::

        class Book(models.Model, Searchable):
            author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Author')
            title = models.CharField("Title", max_length=10)
            rating = models.IntegerField("Rating")
            internal_id = models.CharField(max_length=10)

            searchable = [
                ('author', 'author__name'),  # Search the name instead of the id of the related model. Note the selector syntax
                ('stars', 'rating'),         # Add an extra alias for "rating" that can be used in a query.
                ('internal_id', False),      # Exclude from search
            ]

In other words, add a "searchable" attribute to your models, that lists the
aliases and maps them to a Django field using Django's selector syntax
(underscore-separated field names).

Query from within templates
---------------------------

Using the template tag
~~~~~~~~~~~~~~~~~~~~~~

django-find also provides a template tag that you can use to
render a search field::

    {% load find_tags %}
    {% find object_list %}
    {% for obj in object_list %}
        {{ obj.name }}
    {% endfor %}

You will probably want to use this together with
`dj-pagination <https://github.com/pydanny/dj-pagination>`_ like so::

    {% load find_tags %}
    {% load pagination_tags %}

    {% find object_list %}
    Found {{ object_list.count }} results.

    {% autopaginate object_list %}
    <table>
    {% for obj in object_list %}
        <tr><td>{{ obj.name }}</td></tr>
    {% endfor %}
    </table>

    {% paginate %}

Using provided templates
~~~~~~~~~~~~~~~~~~~~~~~~

django-find comes with some templates that you may find useful::

    {% include 'django_find/headers.html' with object_list=author.objects.all %}

This produces a ``<tr>`` that contains the column headers as returned
by ``Searchable.table_headers()``, e.g.::

    <tr>
    <th>Name</th><th>The title</th><th>Comment</th><th>Stars</th>
    </tr>

Custom field types
------------------

To support your own field types, check the documentation for
:doc:`handlers <handlers>`.
