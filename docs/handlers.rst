Custom Handlers
===============

What are handlers?
------------------

A handler is an object that you can use to define custom
behavior when searching a field of a model.

You might want to use a handler if you are using a custom
model field, or if your query contains information that
requires client-side processing before being passed to
the database.

Example
-------

Lets say you have the following model::

    from django.db import models
    from django_find import Searchable

    class Author(models.Model, Searchable):
        name = models.CharField("Author Name", max_length=50)

    Author.objects.create(name='Robert Frost')

Assuming you want to be able to filter for author names, but need
to translate the name first, e.g.::

    Author.by_query('name:robbie')

You can achieve this by defining a custom handler::

    from django_find.handlers import type_registry, LowerCaseStrFieldHandler

    nicknames = {'robbie': 'Robert Frost'}

    class AuthorNameFieldHandler(LowerCaseStrFieldHandler):
        @classmethod
        def handles(cls, model, field):
            return model._meta.model_name == 'author' and field.name == 'name'

        @classmethod
        def prepare(cls, data):
            return nicknames.get(data, data)

    type_registry.insert(0, AuthorNameFieldHandler)
