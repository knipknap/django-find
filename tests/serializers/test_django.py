from __future__ import absolute_import, print_function
from django.test import TestCase
from django_find.parsers.json import JSONParser
from django_find.serializers.django import DjangoSerializer
from ..models import Author, DummyModel
from ..parsers.test_json import query1, query2

expected_query1 = """(AND: ('name__iexact', 'test'), (NOT (AND: ('book__title__icontains', 'c'))), ('book__chapter__comment__istartswith', 'The '))"""

expected_query2 = """(AND: ('book__chapter__title__icontains', 'foo'))"""

query3 = 'test and updated:"2018-02-01" or updated:^2018-02-02$ added:"^2018-01-01" added:2018-01-02$'
expected_query3 = """(AND: (OR: (AND: (OR: ('hostname__icontains', 'test'), ('address__icontains', 'test'), ('model__icontains', 'test'), (AND: ), (AND: ), ('hostname__icontains', 'test')), ('updated__year', 2018), ('updated__day', 1), ('updated__month', 2)), (AND: ('updated__year', 2018), ('updated__day', 2), ('updated__month', 2)), ('added__gte', datetime.date(2018, 1, 1)), ('added__lte', datetime.date(2018, 1, 2))))"""

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

        query = DummyModel.q_from_query(query3)
        self.assertEqual(str(query), expected_query3)
