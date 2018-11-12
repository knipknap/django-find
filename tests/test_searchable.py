from __future__ import absolute_import
from django.test import TestCase
from .models import Author, DerivedAuthor, SecondAuthor, Book, Chapter, \
        DummyModel, SimpleModel

class SearchableTest(TestCase):
    def setUp(self):
        self.maxDiff = None

    def testGetAliases(self):
        expected = ['name', 'rating', 'author']
        self.assertEqual(expected, Author.get_aliases())

        expected = ['author', 'title', 'comment', 'rating', 'something']
        self.assertEqual(expected, Book.get_aliases())

    def testGetFullNames(self):
        expected = ['Author.name', 'Author.rating', 'Author.author']
        self.assertEqual(expected, Author.get_fullnames())

        expected = ['Book.author', 'Book.title', 'Book.comment',
                    'Book.rating', 'Book.something']
        self.assertEqual(expected, Book.get_fullnames())

    def testTableHeaders(self):
        expected = ['Name', 'rating']
        self.assertEqual(expected, Author.table_headers())

        expected = ['Name', 'The title', 'comment', 'Stars', 'Author']
        self.assertEqual(expected, Book.table_headers())

    def testGetFieldFromSelector(self):
        func = SecondAuthor.get_field_from_selector
        self.assertRaises(Exception, func, 'foo')
        self.assertEqual(func('book__author__name'),
                         (Author, Author._meta.get_field('name')))

    def testGetCaptionFromSelector(self):
        func = SecondAuthor.get_caption_from_selector
        self.assertRaises(Exception, func, 'foo')
        self.assertEqual(func('book__author__name'), 'Name')

    def testGetFieldTypeFromAlias(self):
        func = Author.get_field_type_from_alias
        self.assertRaises(KeyError, func, 'foo')
        self.assertEqual(func('name'), 'LCSTR')
        self.assertEqual(func('author'), 'LCSTR')
        self.assertEqual(func('rating'), 'INT')

    def testGetFieldTypeFromAlias(self):
        func = Author.get_field_type_from_fullname
        self.assertRaises(AttributeError, func, 'foo')
        self.assertEqual(func('Author.name'), 'LCSTR')
        self.assertEqual(func('Book.author'), 'LCSTR')
        self.assertEqual(func('Book.rating'), 'INT')

    def testGetSelectorFromAlias(self):
        func = Author.get_selector_from_alias
        self.assertRaises(KeyError, func, 'foo')
        self.assertEqual(func('name'), 'name')
        self.assertEqual(func('author'), 'name')
        self.assertEqual(func('rating'), 'rating')

    def testGetClassFromFieldName(self):
        func = Author.get_class_from_fullname
        self.assertRaises(KeyError, func, 'no.foo')
        self.assertRaises(AttributeError, func, 'name')
        self.assertEqual(func('Author.name'), (Author, 'name'))
        self.assertEqual(func('Author.author'), (Author, 'author'))
        self.assertEqual(func('Author.rating'), (Author, 'rating'))
        self.assertEqual(func('Book.name'), (Book, 'name'))
        self.assertEqual(func('Book.author'), (Book, 'author'))
        self.assertEqual(func('Book.rating'), (Book, 'rating'))

    def testGetSelectorFromFullname(self):
        func = DummyModel.get_selector_from_fullname
        self.assertRaises(AttributeError, func, 'foo')
        self.assertRaises(KeyError, func, 'DummyModel.foo')
        self.assertEqual(func('DummyModel.host'), 'hostname')
        self.assertEqual(func('DummyModel.model'), 'model')

    def testGetObjectVectorTo(self):
        func = Author.get_object_vector_to
        self.assertEqual(func(Book), [(Author, Book),
                                      (Author, DerivedAuthor, Book),
                                      (Author, SecondAuthor, Book),
                                      (Author, DerivedAuthor, SecondAuthor, Book)])
        self.assertEqual(func(Chapter), [(Author, Book, Chapter),
                                         (Author, DerivedAuthor, Book, Chapter),
                                         (Author, SecondAuthor, Book, Chapter),
                                         (Author, DerivedAuthor, SecondAuthor, Book, Chapter)])

    def testGetQFromQuery(self):
        result = Author.q_from_query('testme AND name:foo')
        query = str(Author.objects.filter(result).query)
        self.assertTrue('WHERE ' in query)
        self.assertTrue('%testme%' in query)

    def testByQueryRaw(self):
        query, fields = SimpleModel.by_query_raw('testme AND comment:foo')
        self.assertTrue('WHERE ' in query.raw_query)
        self.assertTrue('%testme%' in query.raw_query)
        self.failIf('SimpleModel' in query.raw_query)
        self.assertEqual(['SimpleModel.title',
                          'SimpleModel.comment',
                          'SimpleModel.yesno'], fields)

        query, fields = Author.by_query_raw('testme AND name:foo')
        self.assertTrue('WHERE ' in query.raw_query)
        self.assertTrue('%testme%' in query.raw_query)
        self.failIf('Author' in query.raw_query)
        self.failIf('Book' in query.raw_query)
        self.assertEqual(['Author.name', 'Author.rating', 'Author.author'], fields)

        query, fields = Book.by_query_raw('rating:5')
        self.assertTrue('WHERE ' in query.raw_query)
        self.assertTrue('5' in query.raw_query)
        self.failIf('Author' in query.raw_query)
        self.failIf('Book' in query.raw_query)
        self.assertEqual(['Book.rating'], fields)
