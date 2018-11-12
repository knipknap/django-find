from __future__ import absolute_import, print_function
from functools import reduce
from django.db.models import Q
from .serializer import Serializer

class DjangoSerializer(Serializer):
    def __init__(self, model):
        Serializer.__init__(self)
        self.model = model

    def logical_and(self, terms):
        return reduce(lambda x, y: x.__and__(y), terms, Q())

    def logical_or(self, terms):
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
        else:
            return Q(**{selector: value})

    def str_term(self, selector, operator, data):
        return Q(**{selector+'__'+operator: data})

    def lcstr_term(self, selector, operator, data):
        return Q(**{selector+'__i'+operator: data})

    def term(self, name, operator, data):
        if operator == 'any':
            return Q()
        if operator == 'equals':
            operator = 'exact'

        cls, alias = self.model.get_class_from_fullname(name)
        field_type = cls.get_field_type_from_alias(alias)
        selector = self.model.get_selector_from_fullname(name)

        type_map = {'BOOL': self.boolean_term,
                    'INT': self.int_term,
                    'STR': self.str_term,
                    'LCSTR': self.lcstr_term}

        func = type_map.get(field_type)
        if not func:
            raise TypeError('unsupported field type: '+repr(field_type))
        return func(selector, operator, data)
