from __future__ import absolute_import
from django.test import TestCase
from django_find.parsers.json import JSONParser

query1 = '''
{
    "Author":{"name":[[["equals","test"]]]},
    "Book": {"title":[[["notcontains","c"]]]},
    "Chapter": {"comment":[[["startswith","The "]]]}
}
'''
expected1 = """Group(root)
  Term: Author.name equals 'test'
  Not
    Term: Book.title contains 'c'
  Term: Chapter.comment startswith 'The '"""

query2 = '''
{
    "Chapter": {"title":[[["contains","foo"]]]}
}
'''
expected2 = """Group(root)
  Term: Chapter.title contains 'foo'"""

query3 = '''
{
    "Book": {"title":[[["contains","foo"]]]},
    "Chapter": {"title":[[]]}
}
'''
expected3 = """Group(root)
  Term: Book.title contains 'foo'
  Term: Chapter.title any ''"""

class JSONParserTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.parser = JSONParser()

    def testParser(self):
        dom = self.parser.parse(query1)
        self.assertEqual(expected1, dom.dump())

        dom = self.parser.parse(query2)
        self.assertEqual(expected2, dom.dump())
