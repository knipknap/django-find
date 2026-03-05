"""A second app that deliberately defines an Author model with the same
class name as tests.models.Author, connected via a OneToOneField.

This exercises:
  * Name-collision disambiguation in get_class_from_fullname().
  * Forward OneToOneField traversal in get_selector_from_fullname().
"""
from django.db import models
from django_find import Searchable


class Author(models.Model, Searchable):
    """Author extension in 'other_app' — same __name__ as
    search_tests.Author, linked via a OneToOneField."""
    author = models.OneToOneField(
        'search_tests.Author',
        on_delete=models.CASCADE,
        related_name='extended_author',
    )
    genre = models.CharField(max_length=50)
    bio = models.TextField(blank=True, default='')

    searchable = [
        ('genre', 'genre'),
        ('bio', 'bio'),
    ]

    class Meta:
        app_label = 'other_app'
