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

    def term(self, name, operator, data):
        if operator == 'any':
            return Q()
        if operator == 'equals':
            operator = 'exact'

        cls, field_name = self.model.get_class_from_field_name(name)
        target_type, target = cls.get_target_from_name(field_name)
        selector = self.model.get_selector_from_field_name(name)

        if target_type == 'BOOL':
            value = True if data.lower() == 'true' else False
            return Q(**{selector: value})
        elif target_type == 'INT':
            try:
                value = int(data)
            except ValueError:
                return Q()
            else:
                return Q(**{selector: value})
        elif target_type == 'STR':
            return Q(**{selector+'__'+operator: data})
        return Q(**{selector+'__i'+operator: data})  # LCSTR
