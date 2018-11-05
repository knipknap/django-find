from django.db import models
from django_find import Searchable

class DummyModel(models.Model, Searchable):
    hostname = models.CharField(max_length=10)
    address = models.CharField(max_length=10)
    model = models.CharField(max_length=10)

    searchable = [
        ('host', 'hostname'),
    ]

    class Meta:
        app_label = 'search_tests'

class Author(models.Model, Searchable):
    name = models.CharField(max_length=10)
    rating = models.IntegerField()

    searchable = [
        ('author', 'name'),
    ]

    class Meta:
        app_label = 'search_tests'

class DerivedAuthor(Author):
    class Meta:
        app_label = 'search_tests'

class Book(models.Model, Searchable):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    title = models.CharField(max_length=10)
    comment = models.CharField(max_length=10)
    rating = models.IntegerField()

    searchable = [
        ('author', 'author__name'),
    ]

    class Meta:
        app_label = 'search_tests'

class Chapter(models.Model, Searchable):
    book = models.ManyToManyField(Book)
    title = models.CharField(max_length=10)
    comment = models.CharField(max_length=10)

    searchable = [
        ('book', 'book__title'),
    ]

    class Meta:
        app_label = 'search_tests'

class SecondAuthor(models.Model, Searchable):
    author = models.ForeignKey(Author, related_name='author2', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    searchable = [
        ('author', 'author__name'),
        ('book', 'book_title'),
    ]

    class Meta:
        app_label = 'search_tests'

class SimpleModel(models.Model, Searchable):
    title = models.CharField(max_length=10)
    comment = models.CharField(max_length=10)

    class Meta:
        app_label = 'search_tests'
