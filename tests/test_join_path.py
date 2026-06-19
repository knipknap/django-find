"""Regression tests for lossless join-path selection (TIPS-725).

When several equally short join paths connect the requested models,
``get_object_vector_for()`` must prefer a path that does not traverse an
optional relation.  An optional relation (a nullable or reverse foreign key)
becomes a ``LEFT JOIN`` that nulls out the joined columns for rows without a
match, which silently drops those rows once a ``WHERE`` clause references the
columns.

The test models (see ``tests/models.py``) reproduce the original scenario:

    Part -> Gadget -> FarDevice    (all non-null forward FKs: lossless)
    Part <- Alarm  -> FarDevice    (Alarm.part is a reverse relation: lossy)
"""
import json

from django.test import TestCase

from django_find import Searchable
from django_find.refs import (
    count_lossy_edges,
    get_object_vector_for,
    relation_is_lossy,
)

from .models import Alarm, FarDevice, Gadget, Part


class RelationIsLossyTest(TestCase):
    def test_non_null_forward_fk_is_lossless(self):
        self.assertFalse(relation_is_lossy(Part, Gadget))
        self.assertFalse(relation_is_lossy(Gadget, FarDevice))
        self.assertFalse(relation_is_lossy(Alarm, FarDevice))

    def test_reverse_relation_is_lossy(self):
        # Part has no FK to Alarm; Alarm references Part, so a Part may have
        # zero matching Alarm rows.
        self.assertTrue(relation_is_lossy(Part, Alarm))
        self.assertTrue(relation_is_lossy(FarDevice, Gadget))

    def test_nullable_forward_fk_is_lossy(self):
        # Alarm.part is declared null=True.
        self.assertTrue(relation_is_lossy(Alarm, Part))


class CountLossyEdgesTest(TestCase):
    def test_gadget_path_is_lossless(self):
        self.assertEqual(count_lossy_edges((Part, Gadget, FarDevice)), 0)

    def test_alarm_path_is_lossy(self):
        # Only the Part <- Alarm reverse hop is lossy.
        self.assertEqual(count_lossy_edges((Part, Alarm, FarDevice)), 1)


class ObjectVectorSelectionTest(TestCase):
    """The two paths are the same length, so the choice is governed solely by
    the lossless-path preference."""

    def test_module_function_prefers_lossless_path(self):
        vector = get_object_vector_for(Part, [Part, FarDevice], Searchable)
        self.assertEqual(vector, (Part, Gadget, FarDevice))
        self.assertNotIn(Alarm, vector)

    def test_classmethod_prefers_lossless_path(self):
        vector = Part.get_object_vector_for([Part, FarDevice])
        self.assertEqual(vector, (Part, Gadget, FarDevice))
        self.assertNotIn(Alarm, vector)


class SQLJoinPathTest(TestCase):
    """The generated SQL must join FarDevice through Gadget, not Alarm."""

    def setUp(self):
        self.maxDiff = None

    def test_select_joins_through_gadget_not_alarm(self):
        json_string = json.dumps({
            "Part": {"name": [[["equals", "part1"]]]},
            "FarDevice": {"name": [[]]},
        })
        sql, args, fields = Part.sql_from_json(json_string)
        self.assertIn(Gadget._meta.db_table, sql)
        self.assertNotIn(Alarm._meta.db_table, sql)


class FunctionalSearchTest(TestCase):
    """End-to-end: a Part with no Alarm must still resolve its FarDevice
    columns and survive a filter on them."""

    def setUp(self):
        self.far = FarDevice.objects.create(name='dev1')
        self.gadget = Gadget.objects.create(device=self.far)
        self.part = Part.objects.create(gadget=self.gadget, name='part1')
        # Deliberately create no Alarm for this Part.

    def test_far_columns_are_not_nulled(self):
        json_string = json.dumps({
            "Part": {"name": [[["equals", "part1"]]]},
            "FarDevice": {"name": [[]]},
        })
        query, fields = Part.by_json_raw(json_string)
        rows = list(query)
        self.assertEqual(len(rows), 1)
        row = dict(zip(fields, rows[0]))
        self.assertEqual(row['FarDevice.name'], 'dev1')

    def test_filter_on_far_column_returns_the_row(self):
        # This is the exact TIPS-725 symptom: filtering on a related-model
        # column used to return "0 entries" because the lossy join nulled it.
        json_string = json.dumps({
            "Part": {"name": [[["equals", "part1"]]]},
            "FarDevice": {"name": [[["equals", "dev1"]]]},
        })
        query, fields = Part.by_json_raw(json_string)
        rows = list(query)
        self.assertEqual(len(rows), 1)
        self.assertIn('dev1', rows[0])
