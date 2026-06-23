"""
Tests for three search features added on top of django-find:

  1. Multi-value aliases: a single alias may map to several relation paths
     (e.g. a Library's copies live both on the library itself and inside its
     collections); a match on any path matches the row.
  2. JSON search: search a JSONField by key path (metadata__loan_id:1) or as a
     whole document (metadata:value).
  3. Choice translation: search a choices field by its human-readable label,
     expanding to every matching stored code (format:edition -> HC/PB/EB).
"""
from django.test import TestCase
from django_find.parsers.query import QueryParser
from .models import Library, Collection, Copy


class ChoiceTranslationTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.l1 = Library.objects.create(status='O')
        self.c_eb = Copy.objects.create(library=self.l1, format='EB',
                                        shelfmark='REF-1',
                                        metadata={'loan_id': 111})
        self.l2 = Library.objects.create(status='C')
        self.c_au = Copy.objects.create(library=self.l2, format='AU',
                                        shelfmark='AUD-2',
                                        metadata={'loan_id': 222})
        self.l3 = Library.objects.create(status='A')
        self.c_hc = Copy.objects.create(library=self.l3, format='HC',
                                        shelfmark='REF-3',
                                        metadata={'loan_id': 333})

    def _formats(self, query):
        result = Copy.objects.filter(Copy.q_from_query(query))
        return sorted(c.format for c in result)

    def testLabelSubstringExpandsToCodes(self):
        # 'edition' is a substring of the labels of HC, PB and EB.
        self.assertEqual(['EB', 'HC'], self._formats('format:edition'))

    def testRawCodeStillMatches(self):
        self.assertEqual(['HC'], self._formats('format:HC'))

    def testNoMatchYieldsNothing(self):
        self.assertEqual([], self._formats('format:does-not-exist'))

    def testEqualsRequiresFullLabel(self):
        self.assertEqual(['HC'], self._formats('format="Hardcover edition"'))
        # A mere substring does not satisfy the equals operator.
        self.assertEqual([], self._formats('format=edition'))

    def testNegationExcludesAllMatchingCodes(self):
        # Exclude every *edition* code; only the audiobook copy remains.
        self.assertEqual(['AU'], self._formats('format!:edition'))

    def testOwnFieldChoiceOnLibrary(self):
        result = Library.objects.filter(Library.q_from_query('status:Open'))
        self.assertEqual([self.l1.pk], [lib.pk for lib in result])

    def testParserExpandsLabelToOrOfCodes(self):
        parser = QueryParser({'format': 'Copy.format'}, ('format',))
        expected = """Group(root)
  Or
    Term: Copy.format equals 'HC'
    Term: Copy.format equals 'PB'
    Term: Copy.format equals 'EB'"""
        self.assertEqual(expected, parser.parse('format:edition').dump())

    def testParserNegatesExpandedCodes(self):
        parser = QueryParser({'format': 'Copy.format'}, ('format',))
        expected = """Group(root)
  Not
    Or
      Term: Copy.format equals 'HC'
      Term: Copy.format equals 'PB'
      Term: Copy.format equals 'EB'"""
        self.assertEqual(expected, parser.parse('format!:edition').dump())


class JsonSearchTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.c1 = Copy.objects.create(
            library=Library.objects.create(status='O'), format='EB',
            shelfmark='r1', metadata={'loan_id': 111, 'branch': 'CENTRAL'})
        self.c2 = Copy.objects.create(
            library=Library.objects.create(status='C'), format='AU',
            shelfmark='r2', metadata={'loan_id': 222, 'branch': 'ANNEX'})

    def _pks(self, query):
        return [c.pk for c in Copy.objects.filter(Copy.q_from_query(query))]

    def testJsonPathNumber(self):
        self.assertEqual([self.c1.pk], self._pks('metadata__loan_id:111'))

    def testJsonPathString(self):
        self.assertEqual([self.c1.pk], self._pks('metadata__branch:CENTRAL'))

    def testJsonWholeDocument(self):
        self.assertEqual([self.c2.pk], self._pks('metadata:ANNEX'))

    def testParserBuildsJsonPathTerm(self):
        parser = QueryParser({'metadata': 'Copy.metadata'}, ('metadata',))
        expected = """Group(root)
  Term: Copy.metadata__loan_id contains '5'"""
        self.assertEqual(expected, parser.parse('metadata__loan_id:5').dump())


class MultiValueAliasTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        # A copy held directly by the library.
        self.l_direct = Library.objects.create(status='O')
        Copy.objects.create(library=self.l_direct, format='EB',
                            shelfmark='REF-direct', metadata={'loan_id': 1})
        # A copy held only through a collection.
        self.l_collection = Library.objects.create(status='C')
        collection = Collection.objects.create(library=self.l_collection)
        Copy.objects.create(collection=collection, format='AU',
                            shelfmark='REF-shelf', metadata={'loan_id': 2})

    def _libraries(self, query):
        qs = Library.objects.filter(Library.q_from_query(query)).distinct()
        return sorted(lib.pk for lib in qs)

    def testShelfmarkMatchesDirectPath(self):
        self.assertEqual([self.l_direct.pk], self._libraries('shelfmark:REF-direct'))

    def testShelfmarkMatchesCollectionPath(self):
        self.assertEqual([self.l_collection.pk], self._libraries('shelfmark:REF-shelf'))

    def testChoiceMatchesAcrossBothPaths(self):
        # format:edition -> HC/PB/EB; only the direct library has such a copy.
        self.assertEqual([self.l_direct.pk], self._libraries('format:edition'))

    def testJsonMatchesViaCollectionPath(self):
        self.assertEqual([self.l_collection.pk], self._libraries('metadata__loan_id:2'))
