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

# ---------------------------------------------------------------------------
# A small lending-library shape used to exercise three search features:
#   * choice-label search   (format:edition -> HC/PB/EB),
#   * JSON path / whole-document search (metadata__loan_id, metadata:value),
#   * multi-value aliases that reach a copy either directly or via a
#     collection (a Library's own copies, or the copies in its collections).
#
# Library    -- a lending library (the container).
# Collection -- a themed grouping of copies within a library
#               (Collection.library, related_name='collections').
# Copy       -- a single copy of a book.
#   Copy.library    (related_name='copies') -- held directly by the library,
#   Copy.collection (related_name='copies') -- held within a collection.
# ---------------------------------------------------------------------------
LIBRARY_STATUS_CHOICES = [
    ('O', 'Open'),
    ('C', 'Closed'),
    ('A', 'Archived'),
]

COPY_FORMAT_CHOICES = [
    ('HC', 'Hardcover edition'),
    ('PB', 'Paperback edition'),
    ('EB', 'Ebook edition'),
    ('AU', 'Audiobook'),
]

class Library(models.Model, Searchable):
    status = models.CharField(max_length=1, choices=LIBRARY_STATUS_CHOICES)

    searchable = [
        ('status', 'status'),
        ('format', ['copies__format', 'collections__copies__format']),
        ('shelfmark', ['copies__shelfmark', 'collections__copies__shelfmark']),
        ('metadata', ['copies__metadata', 'collections__copies__metadata']),
    ]

    class Meta:
        app_label = 'search_tests'

class Collection(models.Model, Searchable):
    library = models.ForeignKey(Library, on_delete=models.CASCADE,
                                related_name='collections')

    searchable = [
        ('library', 'library__id'),
    ]

    class Meta:
        app_label = 'search_tests'

class Copy(models.Model, Searchable):
    collection = models.ForeignKey(Collection, null=True, blank=True,
                                   on_delete=models.CASCADE, related_name='copies')
    library = models.ForeignKey(Library, null=True, blank=True,
                                on_delete=models.CASCADE, related_name='copies')
    format = models.CharField(max_length=3, choices=COPY_FORMAT_CHOICES)
    shelfmark = models.TextField()
    metadata = models.JSONField(null=True, blank=True, default=None)

    searchable = [
        ('format', 'format'),
        ('shelfmark', 'shelfmark'),
        ('metadata', 'metadata'),
    ]

    class Meta:
        app_label = 'search_tests'
