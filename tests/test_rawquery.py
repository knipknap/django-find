from __future__ import absolute_import
from django.test import TestCase
from django_find.rawquery import PaginatedRawQuerySet
from .models import Author

class PaginatedRawQuerySetTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        for i in range(10):
            Author.objects.create(name='Foo'+str(i), rating=10)
        sql = 'SELECT name, rating FROM '+Author._meta.db_table+' ORDER BY name'
        self.query = PaginatedRawQuerySet(sql)

    def testGetItem(self):
        self.assertEqual(self.query[0], ('Foo0', 10))
        self.assertEqual(list(self.query[0:0]), [])
        self.assertEqual(list(self.query[0:2]), [('Foo0', 10), ('Foo1', 10)])
        self.assertEqual(list(self.query[1:3]), [('Foo1', 10), ('Foo2', 10)])
        self.assertEqual(list(self.query[9:12]), [('Foo9', 10),])
        self.assertEqual(list(self.query[10:11]), [])
        self.assertRaises(IndexError, self.query.__getitem__, -1)
        self.assertRaises(IndexError, self.query.__getitem__, slice(-1, 0))
        self.assertRaises(IndexError, self.query.__getitem__, slice(0, -1))
        self.assertRaises(IndexError, self.query.__getitem__, slice(None, -1))
        self.assertRaises(TypeError, self.query.__getitem__, 'a')

        # Test the result cache.
        self.assertEqual(self.query[0], ('Foo0', 10))
        self.assertEqual(self.query[0], ('Foo0', 10))
        self.assertEqual(list(self.query[0:2]), [('Foo0', 10), ('Foo1', 10)])
        self.assertEqual(list(self.query[0:2]), [('Foo0', 10), ('Foo1', 10)])

    def testQuery(self):
        expected = "SELECT name, rating FROM search_tests_author ORDER BY name"
        self.assertTrue(self.query.query.startswith(expected), self.query.query)

        expected = "SELECT name, rating FROM search_tests_author ORDER BY name LIMIT 3 OFFSET 2"
        self.assertEqual(self.query[2:5].query, expected)

        expected = "SELECT name, rating FROM search_tests_author ORDER BY name"
        self.assertTrue(self.query[:].query.startswith(expected), self.query.query)

    def testLen(self):
        self.assertEqual(len(self.query), 10)
        self.assertEqual(len(self.query), 10) # Cached
        self.assertEqual(len(self.query[2:8]), 6)
        self.assertEqual(len(self.query[:8]), 8)
        self.assertEqual(len(self.query[:]), 10)
        self.assertEqual(len(self.query[1:]), 9)
