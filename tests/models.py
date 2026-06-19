from django.db import models
from django_find import Searchable

class DummyModel(models.Model, Searchable):
    hostname = models.CharField(max_length=10)
    address = models.CharField(max_length=10)
    model = models.CharField(max_length=10)
    added = models.DateField(auto_now_add=True, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True)

    searchable = [
        ('host', 'hostname'),
    ]

    class Meta:
        app_label = 'search_tests'

class Author(models.Model, Searchable):
    name = models.CharField("Name", max_length=10)
    rating = models.IntegerField("Stars")

    searchable = [
        ('author', 'name'),
        ('writer', 'name'),
    ]

    class Meta:
        app_label = 'search_tests'

class DerivedAuthor(Author):
    class Meta:
        app_label = 'search_tests'

class Book(models.Model, Searchable):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='AuthorID')
    title = models.CharField("The title", max_length=10)
    comment = models.CharField("Comment", max_length=10)
    rating = models.IntegerField("Stars")

    searchable = [
        ('author', 'author__name'),
        ('something', 'author'),
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
    yesno = models.BooleanField("Choose yes or no")

    class Meta:
        app_label = 'search_tests'

# ---------------------------------------------------------------------------
# Models that reproduce an ambiguous-join scenario.
#
# There are two equally short paths from Part to FarDevice:
#
#   Part -> Gadget -> FarDevice    (all non-null forward FKs: lossless)
#   Part <- Alarm  -> FarDevice    (Alarm.part is an optional reverse
#                                   relation, so this path is lossy)
#
# get_object_vector_for() must prefer the lossless Gadget path. Otherwise the
# LEFT JOIN through Alarm nulls out the FarDevice columns for parts that have
# no alarm, which silently drops those rows once a filter references the
# FarDevice columns.
# ---------------------------------------------------------------------------
class FarDevice(models.Model, Searchable):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = 'search_tests'

class Gadget(models.Model, Searchable):
    device = models.ForeignKey(FarDevice, on_delete=models.CASCADE)

    class Meta:
        app_label = 'search_tests'

class Part(models.Model, Searchable):
    gadget = models.ForeignKey(Gadget, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)

    class Meta:
        app_label = 'search_tests'

class Alarm(models.Model, Searchable):
    part = models.ForeignKey(Part, null=True, on_delete=models.CASCADE)
    device = models.ForeignKey(FarDevice, on_delete=models.CASCADE)

    class Meta:
        app_label = 'search_tests'
