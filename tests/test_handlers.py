from __future__ import absolute_import
from copy import copy
from django.test import TestCase
from django_find.handlers import type_registry, LowerCaseStrFieldHandler
from .models import Author

nicknames = {'robbie': 'Robert Frost'}

class AuthorNameFieldHandler(LowerCaseStrFieldHandler):
    @classmethod
    def handles(cls, model, field):
        return model._meta.model_name == 'author' and field.name == 'name'

    @classmethod
    def prepare(cls, data):
        return nicknames.get(data, data)

class HandlersTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.old_type_registry = copy(type_registry)

    def tearDown(self):
        del type_registry[:]
        type_registry.extend(self.old_type_registry)

    def testTypeRegistry(self):
        func = Author.get_field_handler_from_alias
        self.assertEqual(func('name'), LowerCaseStrFieldHandler)

        type_registry.insert(0, AuthorNameFieldHandler)
        self.assertEqual(func('name'), AuthorNameFieldHandler)

    def testCustomHandler(self):
        query = str(Author.q_from_query('name:robbie'))
        self.assertEqual(query, "(AND: ('name__icontains', 'robbie'))")

        type_registry.insert(0, AuthorNameFieldHandler)
        query = str(Author.q_from_query('name:robbie'))
        self.assertEqual(query, "(AND: ('name__icontains', 'Robert Frost'))")
