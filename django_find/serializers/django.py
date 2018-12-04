from __future__ import absolute_import, print_function
from functools import reduce
from django.db.models import Q
from .serializer import Serializer
from .util import parse_date, parse_datetime

int_op_map = {'equals': 'exact',
              'contains': 'exact',
              'startswith': 'gte',
              'endswith': 'lte'}

str_op_map = {'equals': 'exact',
              'gt': 'startswith',
              'gte': 'startswith',
              'lt': 'endswith',
              'lte': 'endswith'}

date_op_map = {'startswith': 'gte',
               'endswith': 'lte'}

class DjangoSerializer(Serializer):
    def __init__(self, model):
        Serializer.__init__(self)
        self.model = model

    def logical_and(self, terms):
        terms = [t for t in terms if t]
        return reduce(lambda x, y: x.__and__(y), terms, Q())

    def logical_or(self, terms):
        terms = [t for t in terms if t]
        if not terms:
            return Q()
        return reduce(lambda x, y: x.__or__(y), terms)

    def logical_not(self, terms):
        if len(terms) == 1:
            return ~terms[0]
        return ~self.logical_and(terms)

    def boolean_term(self, selector, operator, data):
        value = data.lower() == 'true'
        return Q(**{selector: value})

    def int_term(self, selector, operator, data):
        try:
            value = int(data)
        except ValueError:
            return Q()
        operator = int_op_map.get(operator, operator)
        if operator == 'exact':
            return Q(**{selector: value})
        return Q(**{selector+'__'+operator: value})

    def str_term(self, selector, operator, data):
        operator = str_op_map.get(operator, operator)
        return Q(**{selector+'__'+operator: data})

    def lcstr_term(self, selector, operator, data):
        operator = str_op_map.get(operator, operator)
        return Q(**{selector+'__i'+operator: data})

    def date_datetime_common(self, selector, operator, thedatetime):
        if not thedatetime:
            return Q()
        operator = date_op_map.get(operator, operator)
        if operator in ('contains', 'equals'):
            return Q(**{selector+'__year': thedatetime.year,
                        selector+'__month': thedatetime.month,
                        selector+'__day': thedatetime.day})
        return Q(**{selector+'__'+operator: thedatetime})

    def date_term(self, selector, operator, data):
        thedate = parse_date(data)
        return self.date_datetime_common(selector, operator, thedate)

    def datetime_term(self, selector, operator, data):
        thedatetime = parse_datetime(data)
        result = self.date_datetime_common(selector, operator, thedatetime)
        if operator != 'equals' or not result:
            return result
        return result&Q(**{selector+'__hour': thedatetime.hour,
                           selector+'__minute': thedatetime.minute})

    def term(self, name, operator, data):
        if operator == 'any':
            return Q()

        cls, alias = self.model.get_class_from_fullname(name)
        handler = cls.get_field_handler_from_alias(alias)
        selector = self.model.get_selector_from_fullname(name)

        type_map = {'BOOL': self.boolean_term,
                    'INT': self.int_term,
                    'STR': self.str_term,
                    'LCSTR': self.lcstr_term,
                    'DATE': self.date_term,
                    'DATETIME': self.datetime_term}

        func = type_map.get(handler.db_type)
        if not func:
            raise TypeError('unsupported field type: '+repr(field_type))
        return func(selector, operator, handler.prepare(data))
