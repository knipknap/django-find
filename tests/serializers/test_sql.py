from __future__ import absolute_import, print_function
from django.test import TestCase
from django_find.parsers.json import JSONParser
from django_find.serializers.sql import SQLSerializer
from ..models import Author
from ..parsers.test_json import query1, expected1, query2, expected2, \
        query3, expected3

expected_select1 = """SELECT DISTINCT search_tests_author.name search_tests_author_name, search_tests_book.title search_tests_book_title, search_tests_chapter.comment search_tests_chapter_comment FROM search_tests_author LEFT JOIN search_tests_book ON search_tests_book.author_id=search_tests_author.id LEFT JOIN search_tests_chapter_book ON search_tests_chapter_book.book_id=search_tests_book.id LEFT JOIN search_tests_chapter ON search_tests_chapter.id=search_tests_chapter_book.chapter_id WHERE (search_tests_author.name='test' AND NOT(search_tests_book.title LIKE '%c%') AND search_tests_chapter.comment LIKE 'the %')"""

expected_select2 = """SELECT DISTINCT search_tests_chapter.title search_tests_chapter_title FROM search_tests_chapter WHERE (search_tests_chapter.title LIKE '%foo%')"""

expected_select3 = """SELECT DISTINCT search_tests_book.title search_tests_book_title, search_tests_chapter.title search_tests_chapter_title FROM search_tests_book LEFT JOIN search_tests_chapter_book ON search_tests_chapter_book.book_id=search_tests_book.id LEFT JOIN search_tests_chapter ON search_tests_chapter.id=search_tests_chapter_book.chapter_id WHERE (search_tests_book.title LIKE '%foo%' AND 1)"""

class SQLSerializerTest(TestCase):
    def setUp(self):
        self.maxDiff = None

    def testSerialize(self):
        parser = JSONParser()
        dom = parser.parse(query1)
        self.assertEqual(expected1, dom.dump())
        select, args = dom.serialize(SQLSerializer(Author))
        self.assertEqual(expected_select1, select % tuple(args))

        parser = JSONParser()
        dom = parser.parse(query2)
        self.assertEqual(expected2, dom.dump())
        select, args = dom.serialize(SQLSerializer(Author))
        self.assertEqual(expected_select2, select % tuple(args))

        parser = JSONParser()
        dom = parser.parse(query3)
        self.assertEqual(expected3, dom.dump())
        select, args = dom.serialize(SQLSerializer(Author))
        self.assertEqual(expected_select3, select % tuple(args))
