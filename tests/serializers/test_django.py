from __future__ import absolute_import, print_function
from django.test import TestCase
from django_find.parsers.json import JSONParser
from django_find.serializers.django import DjangoSerializer
from ..models import Author
from ..parsers.test_json import query1, query2

expected_query1 = """(AND: ('name__iexact', 'test'), (NOT (AND: ('book__title__icontains', 'c'))), ('book__chapter__comment__istartswith', 'The '))"""

expected_query2 = """(AND: ('book__chapter__title__icontains', 'foo'))"""

class DjangoSerializerTest(TestCase):
    def setUp(self):
        self.maxDiff = None

    def testDjangoSQLSerializer(self):
        parser = JSONParser()
        dom = parser.parse(query1)
        query = dom.serialize(DjangoSerializer(Author))
        self.assertEqual(str(query), expected_query1)

        parser = JSONParser()
        dom = parser.parse(query2)
        query = dom.serialize(DjangoSerializer(Author))
        self.assertEqual(str(query), expected_query2)
