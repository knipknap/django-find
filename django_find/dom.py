from __future__ import absolute_import, print_function
from builtins import str
from .tree import Node

class Group(Node):
    def translate_term_names(self, name_map):
        def translate(dom_obj):
            dom_obj.name = name_map.get(dom_obj.name, dom_obj.name)
        self.each(translate, Term)

    def get_term_names(self):
        """
        Returns a flat list of the names of all Terms in the query, in
        the order in which they appear. Filters duplicates.
        """
        field_names = []
        def collect_field_names(dom_obj):
            if not dom_obj.name in field_names:
                field_names.append(dom_obj.name)
        self.each(collect_field_names, Term)
        return field_names

    def auto_leave_scope(self):
        return False

    def optimize(self):
        children = [c.optimize() for c in self.children]
        self.children = [c for c in children if c is not None]
        if not self.children and not self.is_root:
            return None
        if len(self.children) == 1 and not self.is_root:
            return self.children[0]
        return self

    def serialize(self, strategy):
        results = [c.serialize(strategy) for c in self.children]
        if self.is_root:
            return strategy.logical_root_group(self, results)
        return strategy.logical_group(results)

class And(Group):
    def auto_leave_scope(self):
        return True

    def serialize(self, strategy):
        return strategy.logical_and(c.serialize(strategy)
                                    for c in self.children)

class Or(Group):
    def serialize(self, strategy):
        return strategy.logical_or(c.serialize(strategy)
                                   for c in self.children)

class Not(Group):
    def auto_leave_scope(self):
        return True

    def optimize(self):
        children = [c.optimize() for c in self.children]
        self.children = [c for c in children if c is not None]
        if not self.children and not self.is_root:
            return None
        return self

    def serialize(self, strategy):
        children = [c.serialize(strategy) for c in self.children]
        return strategy.logical_not(children)

class Term(Node):
    def __init__(self, name, operator, data):
        Node.__init__(self)
        self.name = name
        self.operator = str(operator)
        self.data = str(data)

    def optimize(self):
        return self

    @classmethod
    def from_query_value(cls, name, value):
        if value.startswith('^') and value.endswith('$'):
            value = value[1:-1]
            operator = 'equals'
        elif value.startswith('^'):
            value = value[1:]
            operator = 'startswith'
        elif value.endswith('$'):
            value = value[:-1]
            operator = 'endswith'
        else:
            operator = 'contains'
        return Term(name, operator, value)

    def each(self, func, node_type):
        if node_type is None or isinstance(self, node_type):
            func(self)

    def dump(self, indent=0):
        return [(indent * '  ')
                + self.__class__.__name__ + ': '
                + self.name + ' ' + self.operator + ' ' + repr(self.data)]

    def serialize(self, strategy):
        return strategy.term(self.name, self.operator, self.data)
