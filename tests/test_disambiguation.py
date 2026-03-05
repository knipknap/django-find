"""Tests for the name-collision disambiguation in get_class_from_fullname().

Two Django apps (search_tests and other_app) each define a model called
"Author".  The other_app.Author is connected to search_tests.Author via
a OneToOneField (a common pattern for extending a model from another app).

The disambiguation logic works in three tiers:

1. **Qualified form** — ``app_label.Model.field`` always resolves
   unambiguously via ``_meta.label``.
2. **Same-app context** — when the calling ``cls`` shares its
   ``app_label`` with exactly one of the matching models, that model
   is preferred (this is how the JSON parser + serializer pipeline
   works: the serializer is instantiated with a specific model).
3. **Ambiguity error** — if neither tier resolves to a single model,
   a ``KeyError`` is raised listing the candidates.
"""
import json
from collections import OrderedDict
from django.test import TestCase

from django_find.parsers.json import JSONParser
from django_find.serializers.django import DjangoSerializer
from .models import Author as SearchTestsAuthor, Book
from .other_app.models import Author as OtherAppAuthor


class ClassnameDisambiguationTest(TestCase):
    """Verify that same-named models in different apps can be
    distinguished via qualified fullnames and same-app context."""

    # -- Tier 1: qualified form ------------------------------------------

    def test_qualified_fullname_resolves_search_tests_author(self):
        cls, alias = SearchTestsAuthor.get_class_from_fullname(
            'search_tests.Author.name'
        )
        self.assertIs(cls, SearchTestsAuthor)
        self.assertEqual(alias, 'name')

    def test_qualified_fullname_resolves_other_app_author(self):
        cls, alias = OtherAppAuthor.get_class_from_fullname(
            'other_app.Author.genre'
        )
        self.assertIs(cls, OtherAppAuthor)
        self.assertEqual(alias, 'genre')

    def test_cross_app_qualified_resolution(self):
        """Qualified form works even when cls is in a different app."""
        cls, alias = SearchTestsAuthor.get_class_from_fullname(
            'other_app.Author.genre'
        )
        self.assertIs(cls, OtherAppAuthor)
        self.assertEqual(alias, 'genre')

    # -- Tier 2: same-app context ----------------------------------------

    def test_short_name_resolved_by_same_app_context(self):
        """When cls is in the same app as one of the matches, it wins."""
        cls, alias = SearchTestsAuthor.get_class_from_fullname('Author.name')
        self.assertIs(cls, SearchTestsAuthor)
        self.assertEqual(alias, 'name')

    def test_short_name_resolved_by_other_app_context(self):
        """Same-app logic works for the other app too."""
        cls, alias = OtherAppAuthor.get_class_from_fullname('Author.genre')
        self.assertIs(cls, OtherAppAuthor)
        self.assertEqual(alias, 'genre')

    def test_related_model_in_same_app_resolves(self):
        """Book (search_tests) resolving Author.name picks search_tests.Author."""
        cls, alias = Book.get_class_from_fullname('Author.name')
        self.assertIs(cls, SearchTestsAuthor)
        self.assertEqual(alias, 'name')

    # -- Tier 3: unresolvable ambiguity ----------------------------------

    def test_unambiguous_short_name_still_works(self):
        """Models with a unique __name__ resolve via short form."""
        cls, alias = Book.get_class_from_fullname('Book.title')
        self.assertIs(cls, Book)
        self.assertEqual(alias, 'title')

    # -- get_classname / get_fullnames -----------------------------------

    def test_get_classname_qualified_when_ambiguous(self):
        """get_classname() returns app_label.Model when there is a collision."""
        self.assertEqual(SearchTestsAuthor.get_classname(), 'search_tests.Author')
        self.assertEqual(OtherAppAuthor.get_classname(), 'other_app.Author')

    def test_get_classname_short_when_unique(self):
        """get_classname() returns bare __name__ when there is no collision."""
        self.assertEqual(Book.get_classname(), 'Book')

    def test_get_fullnames_uses_qualified_classname(self):
        """get_fullnames() returns qualified names when there's a collision."""
        fullnames = OtherAppAuthor.get_fullnames()
        self.assertTrue(all(fn.startswith('other_app.Author.') for fn in fullnames))
        self.assertIn('other_app.Author.genre', fullnames)
        self.assertIn('other_app.Author.bio', fullnames)

    # -- get_selector_from_fullname --------------------------------------

    def test_selector_from_qualified_fullname(self):
        """ORM selectors must be correct even when using qualified form."""
        selector = Book.get_selector_from_fullname(
            'search_tests.Author.name'
        )
        self.assertEqual(selector, 'author__name')

    def test_selector_from_short_fullname_via_same_app(self):
        """ORM selectors work with short names when same-app context resolves."""
        selector = Book.get_selector_from_fullname('Author.name')
        self.assertEqual(selector, 'author__name')

    # -- OneToOneField relationship tests --------------------------------

    def test_onetoone_forward_selector(self):
        """From other_app.Author, resolve a field on search_tests.Author
        by traversing the OneToOneField in the forward direction."""
        selector = OtherAppAuthor.get_selector_from_fullname(
            'search_tests.Author.name'
        )
        self.assertEqual(selector, 'author__name')

    def test_onetoone_object_vector(self):
        """get_object_vector_to finds the path through the OneToOneField."""
        paths = OtherAppAuthor.get_object_vector_to(SearchTestsAuthor)
        self.assertTrue(len(paths) >= 1)
        shortest = paths[0]
        self.assertEqual(shortest[0], OtherAppAuthor)
        self.assertEqual(shortest[-1], SearchTestsAuthor)

    def test_onetoone_query_own_field(self):
        """A query on an own field of the OneToOne-linked model works."""
        q = OtherAppAuthor.q_from_query('genre:Fantasy')
        query_str = str(q)
        self.assertIn('genre', query_str)
        self.assertIn('Fantasy', query_str)

    # -- JSON parser + DjangoSerializer end-to-end -----------------------

    def test_json_parser_with_short_classnames(self):
        """The JSON input API uses bare class names.  The serializer's
        own model provides the same-app context to resolve them."""
        query_json = json.dumps(OrderedDict([
            ("Author", {"name": [[["contains", "Tolkien"]]]}),
        ]))
        dom = JSONParser().parse(query_json)
        q = dom.serialize(DjangoSerializer(SearchTestsAuthor))
        self.assertIn('name__icontains', str(q))
        self.assertIn('Tolkien', str(q))

    # -- q_from_query (end-to-end) ---------------------------------------

    def test_query_via_qualified_author(self):
        """A full end-to-end query on the qualified model must not crash."""
        q = OtherAppAuthor.q_from_query('genre:Fantasy')
        query_str = str(OtherAppAuthor.objects.filter(q).query)
        self.assertIn('genre', query_str)
        self.assertIn('Fantasy', query_str)
