from __future__ import absolute_import, print_function
from django.test import TestCase
from django_find import Searchable
from django_find.refs import get_subclasses, child_classes, parent_classes, \
        get_field_to, get_join_for, get_object_vector_to
from .models import Author, DerivedAuthor, SecondAuthor, Book, Chapter

class RefsTest(TestCase):
    def setUp(self):
        self.maxDiff = None

    def testGetSubClasses(self):
        result = get_subclasses(Searchable)
        self.assertIn(Author, result)
        self.assertIn(Book, result)
        self.assertIn(DerivedAuthor, result)
        self.assertNotIn(RefsTest, result)

    def testChildClasses(self):
        #children = child_classes(Author)
        #self.assertEqual(children, [Book, SecondAuthor])
        children = child_classes(Book)
        self.assertEqual(children, [Chapter, SecondAuthor])

    def testParentClasses(self):
        parents = parent_classes(Author)
        self.assertEqual(parents, [])
        parents = parent_classes(Book)
        self.assertEqual(parents, [Author])
        parents = parent_classes(SecondAuthor)
        self.assertEqual(parents, [Author, Book])

    def testGetFieldTo(self):
        field = get_field_to(Author, Book)
        self.assertEqual(field, None)
        field = get_field_to(Book, Author)
        self.assertEqual(field, Book._meta.get_field('author'))

    def testGetObjectVectorTo(self):
        self.assertEqual(get_object_vector_to(Author, Book, Searchable),
                         [(Author, Book),
                          (Author, DerivedAuthor, Book),
                          (Author, SecondAuthor, Book),
                          (Author, DerivedAuthor, SecondAuthor, Book)])

        self.assertEqual(get_object_vector_to(Author, Chapter, Searchable),
                         [(Author, Book, Chapter),
                          (Author, DerivedAuthor, Book, Chapter),
                          (Author, SecondAuthor, Book, Chapter),
                          (Author, DerivedAuthor, SecondAuthor, Book, Chapter)])

        self.assertEqual(get_object_vector_to(Author, SecondAuthor, Searchable),
                         [(Author, SecondAuthor),
                          (Author, DerivedAuthor, SecondAuthor),
                          (Author, Book, SecondAuthor),
                          (Author, DerivedAuthor, Book, SecondAuthor)])

    def testGetJoinFor(self):
        expected = [(u'search_tests_author', None, None),
                    (u'search_tests_book', u'author_id', u'search_tests_author.id'),
                    (u'search_tests_chapter_book', u'book_id', u'search_tests_book.id'),
                    (u'search_tests_chapter', u'id', u'search_tests_chapter_book.chapter_id')]
        self.assertEqual(get_join_for((Author, Book, Chapter)), expected)

        expected = [(u'search_tests_chapter', None, None),
                    (u'search_tests_chapter_book', u'chapter_id', u'search_tests_chapter.id'),
                    (u'search_tests_book', u'id', u'search_tests_chapter_book.book_id'),
                    (u'search_tests_author', u'id', u'search_tests_book.author_id'),
                    (u'search_tests_secondauthor', u'author_id', u'search_tests_author.id')]
        self.assertEqual(get_join_for((Chapter, Book, Author, SecondAuthor)), expected)
