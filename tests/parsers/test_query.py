
from django.test import TestCase
from django_find.parsers.query import QueryParser

name_map = {'host': 'Device.metadata_id',
            'model': 'Device.model',
            'interface': 'Unit.interface'}

query1 = 'host:^test (model:foo or interface:bar)'
expected_dom1 = """Group(root)
  Term: Device.metadata_id startswith 'test'
  Or
    Term: Device.model contains 'foo'
    Term: Unit.interface contains 'bar'"""

query2 = 'test (model:foo or interface:bar$)'
expected_dom2 = """Group(root)
  Or
    Term: Device.metadata_id contains 'test'
    Term: Device.model contains 'test'
    Term: Device.model contains 'foo'
    Term: Unit.interface endswith 'bar'"""

query3 = 'host<z host>a host!:no host:yes host!=no host=yes host>=c host<=g host<>no'
expected_dom3 = """Group(root)
  Term: Device.metadata_id lt 'z'
  Term: Device.metadata_id gt 'a'
  Not
    Term: Device.metadata_id contains 'no'
  Term: Device.metadata_id contains 'yes'
  Not
    Term: Device.metadata_id equals 'no'
  Term: Device.metadata_id equals 'yes'
  Term: Device.metadata_id gte 'c'
  Term: Device.metadata_id lte 'g'
  Not
    Term: Device.metadata_id equals 'no'"""
# The 'not' keyword has the highest precedence: it binds only to the next
# single term, even without brackets, so the terms that follow are siblings.
query4 = 'host:a and not model:b and interface:c'
expected_dom4 = """Group(root)
  And
    Term: Device.metadata_id contains 'a'
    Not
      Term: Device.model contains 'b'
    Term: Unit.interface contains 'c'"""

# When the operand is parenthesized, 'not' binds to the whole group only.
query5 = 'not (model:b or interface:c) and host:a'
expected_dom5 = """Group(root)
  And
    Not
      Or
        Term: Device.model contains 'b'
        Term: Unit.interface contains 'c'
    Term: Device.metadata_id contains 'a'"""
class QueryParserTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.parser = QueryParser(name_map, ('host', 'model'))

    def testParser(self):
        dom = self.parser.parse(query1)
        self.assertEqual(expected_dom1, dom.dump())

        dom = self.parser.parse(query2)
        self.assertEqual(expected_dom2, dom.dump())

        dom1 = self.parser.parse("host:^test$")
        dom2 = self.parser.parse("host=test")
        self.assertEqual(dom1.dump(), dom2.dump())

        dom = self.parser.parse(query3)
        self.assertEqual(expected_dom3, dom.dump())

        dom = self.parser.parse(query4)
        self.assertEqual(expected_dom4, dom.dump())

        dom = self.parser.parse(query5)
        self.assertEqual(expected_dom5, dom.dump())
