from __future__ import absolute_import, print_function
import re
from .parser import Parser
from ..dom import Group, And, Or, Not, Term

tokens = [('and', re.compile(r'and\b', re.I)),
          ('or', re.compile(r'or\b', re.I)),
          ('not', re.compile(r'not\b', re.I)),
          ('openbracket', re.compile(r'\(')),
          ('closebracket', re.compile(r'\)')),
          ('whitespace', re.compile(r'\s+')),
          ('field', re.compile(r'([\w\-]+):')),
          ('word', re.compile(r'"([^"]*)"')),
          ('word', re.compile(r'([^"\s\\\'\)]+)')),
          ('unknown', re.compile(r'.'))]

def open_scope(scopes, scope):
    scopes.append(scopes[-1].add(scope))

def close_scope(scopes):
    while scopes[-1].auto_leave_scope() and not scopes[-1].is_root:
        scopes.pop()

class QueryParser(Parser):
    def __init__(self, fields, default):
        """
        Fields is a map that translates aliases to something like
        Book.author.
        """
        Parser.__init__(self, tokens)
        self.fields = fields
        self.default = default or fields
        for name in self.default:
            if name not in self.fields:
                raise AttributeError('constructor argument "default" contains'\
                    +' "{}", which is not also in "fields"'.format(name))

    def parse_word(self, scopes, match):
        child = Or()
        for name in self.default:
            name = self.fields[name]
            child.add(Term.from_query_value(name, match.group(1)))
        scopes[-1].add(child)
        close_scope(scopes)

    def parse_field(self, scopes, match):
        field_name = match.group(1).lower()
        field = self.fields.get(field_name)
        if field is None:
            self.parse_word(scopes, match)
            return

        # A field value is required.
        token, match = self._get_next_token()
        try:
            value = [match.group(1)]
        except IndexError:
            return
        scopes[-1].add(Term.from_query_value(field, " ".join(value)))
        close_scope(scopes)

    def parse_boolean(self, scopes, dom_cls, match):
        try:
            last_term = scopes[-1].pop()
        except IndexError:
            pass
        else:
            open_scope(scopes, dom_cls(last_term))

    def parse_and(self, scopes, match):
        self.parse_boolean(scopes, And, match)

    def parse_or(self, scopes, match):
        self.parse_boolean(scopes, Or, match)

    def parse_not(self, scopes, match):
        open_scope(scopes, Not())

    def parse_openbracket(self, scopes, match):
        open_scope(scopes, Group())

    def parse_closebracket(self, scopes, match):
        # Leave the current group.
        while type(scopes[-1]) != type(Group) and not scopes[-1].is_root:
            scopes.pop()
        if not scopes[-1].is_root:
            scopes.pop()

        # Auto-leave the parent scope (if necessary).
        close_scope(scopes)

    def parse_whitespace(self, scopes, match):
        pass

    def parse(self, query):
        self._reset()
        self.input = query.strip()
        result = Group(is_root=True)
        scopes = [result]
        token, match = self._get_next_token()

        while token != 'EOF':
            parse_func = getattr(self, 'parse_'+token)
            parse_func(scopes, match)
            token, match = self._get_next_token()

        return result.optimize()
