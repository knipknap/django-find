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
django-find supports the following queries:

- ``hello world`` (searches all fields for hello and world)
- ``author:robert OR title:road`` (searches the field "author" for "robert", and "title" for "road")
- ``author:"robert frost" and (title:road or chapter:2)`` (the AND is optional, it is implied by default)
- ``^robert`` (find anything that starts with "robert")
- ``robert$`` (find anything that ends with "robert")
- ``^robert$ and not title:road`` (find anything that equals "robert" and not the title "road")
- ``test (name:foo and (book:one or book:two) and (chapter:10 or chapter:12 or chapter:13))`` (arbitrary nesting is supported)

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

That is all, your models now provide the following methods::

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
