from __future__ import absolute_import, print_function
import re
from .parser import Parser
from ..dom import Group, And, Or, Not, Term

tokens = [('and',          re.compile(r'and\b', re.I)),
          ('or',           re.compile(r'or\b',  re.I)),
          ('not',          re.compile(r'not\b', re.I)),
          ('openbracket',  re.compile(r'\(')),
          ('closebracket', re.compile(r'\)')),
          ('whitespace',   re.compile(r'\s+')),
          ('field',        re.compile(r'([\w\-]+):')),
          ('word',         re.compile(r'"([^"]*)"')),
          ('word',         re.compile(r'([^"\s\\\'\)]+)')),
          ('unknown',      re.compile(r'.'))]

boolean = {'and': And, 'or': Or, 'not': Not}

def open_scope(scopes, scope):
    scopes.append(scopes[-1].add(scope))

def close_scope(scopes):
    while scopes[-1].auto_leave_scope() and not scopes[-1].is_root:
        scopes.pop()

class QueryParser(Parser):
    def __init__(self, fields, default):
        """
        Field is a map that translates aliases to something like Book.author.
        """
        Parser.__init__(self, tokens)
        self.fields = fields
        self.default = default or fields
        for name in self.default:
            if name not in self.fields:
                raise AttributeError('constructor argument "default" contains'\
                    +' "{}", which is not also in "fields"'.format(name))

    def parse(self, query):
        self._reset()
        self.input = query.strip()
        result = Group(is_root=True)
        scopes = [result]
        token, match = self._get_next_token()

        while token != 'EOF':
            if token == 'word':
                child = Or()
                for name in self.default:
                    name = self.fields[name]
                    child.add(Term.from_query_value(name, match.group(1)))
                scopes[-1].add(child)
                close_scope(scopes)
                token, match = self._get_next_token()
                continue

            elif token == 'field':
                # If the given field does not exists, treat it like a
                # search term.
                field_name = match.group(1).lower()
                field = self.fields.get(field_name)
                if field is None:
                    token = 'word'
                    continue

                # A field value is required.
                token, match = self._get_next_token()
                try:
                    value = [match.group(1)]
                except IndexError:
                    token, match = self._get_next_token()
                    continue

                scopes[-1].add(Term.from_query_value(field, " ".join(value)))
                close_scope(scopes)

                token, match = self._get_next_token()
                continue

            elif token == 'and' or token == 'or':
                try:
                    last_term = scopes[-1].pop()
                except IndexError:
                    pass
                else:
                    dom_cls = boolean[token]
                    open_scope(scopes, dom_cls(last_term))
                token, match = self._get_next_token()
                continue

            elif token == 'not':
                open_scope(scopes, Not())
                token, match = self._get_next_token()
                continue

            elif token == 'openbracket':
                open_scope(scopes, Group())
                token, match = self._get_next_token()
                continue

            elif token == 'closebracket':
                # Leave the current group.
                while type(scopes[-1]) != type(Group) and not scopes[-1].is_root:
                    scopes.pop()
                if not scopes[-1].is_root:
                    scopes.pop()

                # Auto-leave the parent scope (if necessary).
                close_scope(scopes)
                token, match = self._get_next_token()
                continue

            elif token == 'whitespace':
                token, match = self._get_next_token()
                continue

            elif token == 'EOF':
                break

            else:
                #raise Exception('BUG: Unknown token ' + str(token))
                token, match = self._get_next_token()
                continue

        return result.optimize()
