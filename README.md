# django-find

[![Build Status](https://travis-ci.org/knipknap/django-find.svg?branch=master)](https://travis-ci.org/knipknap/django-find)
[![Coverage Status](https://coveralls.io/repos/github/knipknap/django-find/badge.svg?branch=master)](https://coveralls.io/github/knipknap/django-find?branch=master)
[![Code Climate](https://lima.codeclimate.com/github/knipknap/django-find/badges/gpa.svg)](https://lima.codeclimate.com/github/knipknap/django-find)
[![Documentation Status](https://readthedocs.org/projects/django-find/badge/?version=latest)](http://django-find.readthedocs.io/en/latest/?badge=latest)

## Summary

**django-find** is a Django app that makes it easy to add complex
search/filter functionality for the models in your project.
It supports two different ways to search your Django models:
Query-based, or JSON-based.

**django-find** is not a full text search engine, it searches the fields
of your models. In other words, it filters on your models and provides
tabular data as a result.

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

To make it easy to do complex searches spanning multiple models, another
method is provided. For example, you may want to allow for custom searches
that let the user choose which models and columns to include.
In other words, a user interface like this:

![Custom Search](https://raw.githubusercontent.com/knipknap/django-find/master/docs/_static/custom.png)

For this, a JSON-based search functionality is provided:

```
{
    "Author":{"name":[[["equals","test"]]]},
    "Book": {"title":[[["notcontains","c"]]]},
    "Chapter": {"content":[[["startswith","The "]]]}
}
```

django-find is smart in figuring out how to join those models
together and return a useful result.


## Quick start

Enabling the functionality is as simple as adding the "Searchable"
mixin. Example:

```python
from django.db import models
from django_find import Searchable

class Author(models.Model, Searchable):
    name = models.CharField("Author Name", max_length=10)

class Book(models.Model, Searchable):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Author')
    title = models.CharField("Title", max_length=80)
    rating = models.IntegerField("Rating")
    internal_id = models.CharField(max_length=10)
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
would with a Django QuerySet, as it supports slicing and
pagination.

## Documentation

Full documentation, including installation instructions, is here:

http://django-find.readthedocs.io
