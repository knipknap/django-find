# django-searchable

## Summary

django-netparser is a Django app that makes it easy to add complex
search functionality to your project. It supports two different ways
to search your Django models: Query-based, or JSON-based.

### Query-based search

By query-based, we mean that you can use statements like these
to search your model:

- `hello world` (searches all fields for hello and world)
- `author:robert OR title:road` (searches the field "author" for "robert", and "title" for "road")
- `author:"robert frost" and (title:road or chapter:2)`
- `^robert` (find anything that starts with "robert")
- `robert$` (find anything that ends with "robert")
- `^robert$ and not title:road` (find anything that equals "robert" and not the title "road")

In other words, you can write anything from super-simple text based
searches, to complex boolean logic.

### JSON-based search

To make it easy to do complex searches spanning multiple models, a
JSON-based search functionality is provided:

```
{
    "Author":{"name":[[["equals","test"]]]},
    "Book": {"title":[[["notcontains","c"]]]},
    "Chapter": {"content":[[["startswith","The "]]]}
}
```

django-searchable is smart in figuring out how to join those models
together and return a useful search results.

## Example

Enabling the functionality is as simple as the following:

1. Make sure your model inherits the `Searchable` mixin. A word of
   caution: Inherit from models.Model first, then Searchable.
2. Add a "searchable" attribute to your models, that lists the
   aliases and maps them to a Django field using Django's selector
   syntax (underscore-separated field names).

Example:

```python
from django.db import models
from django_searchable import Searchable

class Author(models.Model, Searchable):
    name = models.CharField("Author Name", max_length=10)

    searchable = [
        ('author', 'name'),
        ('name', 'name'),
    ]

class Book(models.Model, Searchable):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    title = models.CharField("Title", max_length=10)
    rating = models.IntegerField()

    searchable = [
        ('author', 'author__name'),  # Note the selector syntax
        ('title', 'title'),
        ('rating', 'rating'),
    ]
```

That is all, your models now provide the following methods:

```python
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
```

You can pass the PaginatedRawQuerySet to Django templates as you
would with a Django QuerySet, as it supports slicing/pagination.

## Quick start

1. Add "django\_searchable" to your `INSTALLED_APPS` setting like this::

    ```python
    INSTALLED_APPS = [
        ...
        'django_searchable',
    ]
    ```

2. Include the django\_searchable URLconf in your project urls.py like this::

    ```python
    path('django_searchable/', include('django_searchable.urls')),
    ```

3. Run `python manage.py migrate` to create the django\_searchable models.
