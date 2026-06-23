import re
from django.db.models import JSONField
from django_find import models
from collections import OrderedDict
from .parser import Parser
from ..dom import Group, And, Or, Not, Term

operators = OrderedDict((
    ('!=', 'notequals'),
    ('<>', 'notequals'),
    ('>=', 'gte'),
    ('=>', 'gte'),
    ('>', 'gt'),
    ('<=', 'lte'),
    ('=<', 'lte'),
    ('<', 'lt'),
    (':', 'contains'),
    ('!:', 'notcontains'),
    ('=', 'equals'),
))

operators_str = '|'.join(list(operators.keys()))
tokens = [
    ('and', re.compile(r'and\b', re.I)),
    ('or', re.compile(r'or\b', re.I)),
    ('not', re.compile(r'not\b', re.I)),
    ('openbracket', re.compile(r'\(')),
    ('closebracket', re.compile(r'\)')),
    ('whitespace', re.compile(r'\s+')),
    ('field', re.compile(r'([\w\-]+)({})'.format(operators_str))),
    ('word', re.compile(r'"([^"]*)"')),
    ('word', re.compile(r'([^"\s\\\'\)]+)')),
    ('unknown', re.compile(r'.'))
]

def open_scope(scopes, scope):
    scopes.append(scopes[-1].add(scope))

def close_scope(scopes):
    while scopes[-1].auto_leave_scope() and not scopes[-1].is_root:
        scopes.pop()

def op_from_word(word):
    if word.startswith('^') and word.endswith('$'):
        return word[1:-1], 'equals'
    elif word.startswith('^'):
        return word[1:], 'startswith'
    elif word.endswith('$'):
        return word[:-1], 'endswith'
    return word, 'contains'

def get_term_from_op(field, operator, value):
    op = operators.get(operator)

    if op == 'contains':
        value, op = op_from_word(value)
    if op == 'notcontains':
        value, op = op_from_word(value)
        op = 'not'+op

    if op.startswith('not'):
        return Not(Term(field, op[3:], value))
    return Term(field, op, value)

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
        self.parse_or(scopes, ())
        child = Or()
        for name in self.default:
            name = self.fields[name]
            value, operator = op_from_word(match.group(1))
            child.add(Term(name, operator, value))
        scopes[-1].add(child)
        close_scope(scopes)

    def parse_field(self, scopes, match):
        field_name = match.group(1).lower()
        field = self.fields.get(field_name)
        if field is None:
            # The name may be a JSON key path, e.g. metadata__loan_id, where
            # 'metadata' is a registered alias pointing at a JSONField.
            json_name = self._json_path_fullname(field_name)
            if json_name is None:
                self.parse_word(scopes, match)
                return
            op = match.group(2)
            token, value_match = self._get_next_token()
            try:
                value = value_match.group(1)
            except (IndexError, AttributeError):
                return
            term = get_term_from_op(json_name, op, value)
            scopes[-1].add(term)
            close_scope(scopes)
            return

        # A field value is required.
        op = match.group(2)
        token, value_match = self._get_next_token()
        try:
            value = value_match.group(1)
        except (IndexError, AttributeError):
            return

        # When the field has choices, let the user search by the human-readable
        # display label, expanding to every matching stored value, e.g.
        # format:edition -> (format=HC OR format=PB OR format=EB).
        node = self._build_choice_node(field, op, value)
        if node is not None:
            scopes[-1].add(node)
            close_scope(scopes)
            return

        term = get_term_from_op(field, op, value)
        scopes[-1].add(term)
        close_scope(scopes)

    @staticmethod
    def _field_from_fullname(fullname):
        """
        Resolve a fullname (e.g. 'Copy.format') to its Django field, or
        None when it cannot be resolved (e.g. the parser was built with a
        synthetic name map that does not map to real Searchable models).
        """
        try:
            cls, alias = models.Searchable.get_class_from_fullname(fullname)
            return cls.get_field_from_alias(alias)
        except Exception:
            return None

    def _json_path_fullname(self, field_name):
        """
        If field_name is '<base>__<path>' where <base> is a registered alias
        pointing at a JSONField, return the fullname carrying the JSON path,
        e.g. 'Copy.metadata__loan_id'. Otherwise return None.
        """
        if '__' not in field_name:
            return None
        base, path = field_name.split('__', 1)
        base_fullname = self.fields.get(base)
        if base_fullname is None:
            return None
        field = self._field_from_fullname(base_fullname)
        if not isinstance(field, JSONField):
            return None
        return base_fullname + '__' + path

    def _build_choice_node(self, fullname, operator, value):
        """
        For a choices field, expand a search by display label into an OR of
        exact-match terms over the matching stored codes. Returns a DOM node
        (Or, or Not(Or)), or None when no translation applies so the caller
        falls back to the normal term.

        ``:`` / ``!:`` (contains) match the label or code as a case-insensitive
        substring; ``=`` / ``!=`` (equals) require a full case-insensitive
        match of the label or code.
        """
        op = operators.get(operator)
        if op not in ('contains', 'equals', 'notcontains', 'notequals'):
            return None
        field = self._field_from_fullname(fullname)
        if field is None:
            return None
        choices = field.flatchoices or []
        if not choices:
            return None
        needle = value.lower()
        exact = op in ('equals', 'notequals')
        codes = []
        for code, label in choices:
            code_s, label_s = str(code), str(label)
            if exact:
                matched = needle == code_s.lower() or needle == label_s.lower()
            else:
                matched = needle in code_s.lower() or needle in label_s.lower()
            if matched:
                codes.append(code_s)
        if not codes:
            # Nothing matched; fall back to the untranslated term, which yields
            # no rows just like before (stored values are the codes).
            return None
        or_group = Or()
        for code in codes:
            or_group.add(Term(fullname, 'equals', code))
        if op in ('notcontains', 'notequals'):
            not_group = Not()
            not_group.add(or_group)
            return not_group
        return or_group

    def parse_boolean(self, scopes, dom_cls, match):
        try:
            if scopes[-1].is_logical() and dom_cls.precedence() < scopes[-1].precedence():
                scopes.pop()
            if type(scopes[-1]).__name__ == dom_cls.__name__:
                return
            last_term = scopes[-1].pop()
        except IndexError:
            open_scope(scopes, dom_cls())
        else:
            open_scope(scopes, dom_cls(last_term))

    def parse_and(self, scopes, match):
        self.parse_boolean(scopes, And, match)

    def parse_or(self, scopes, match):
        self.parse_boolean(scopes, Or, match)

    def parse_term(self, token, scopes, match):
        try:
            parse_func = getattr(self, 'parse_'+token)
            parse_func(scopes, match)
        except AttributeError:
            pass

    def add_logical_scope(self, scopes, match):
        """
        Reads exactly one operand that follows a 'not' keyword into the
        current scope. The operand is either a single term ('word' or
        'field:value') or a parenthesized group.

        Binding 'not' to a single operand (instead of greedily consuming the
        rest of the expression) is what gives 'not' the highest precedence:
        it binds tighter than 'and' and 'or' without requiring brackets, so
        e.g. "a and not b and c" is parsed as "a and (not b) and c".
        """
        self.parse_openbracket(scopes, match)

        # Skip any whitespace between 'not' and its operand.
        token, match = self._get_next_token()
        while token == 'whitespace':
            token, match = self._get_next_token()

        if token == 'openbracket':
            # The operand is a parenthesized group: consume tokens until the
            # matching closing bracket, honouring nested brackets.
            depth = 1
            self.parse_term(token, scopes, match)
            while depth > 0:
                token, match = self._get_next_token()
                if token == 'EOF':
                    break
                if token == 'openbracket':
                    depth += 1
                elif token == 'closebracket':
                    depth -= 1
                self.parse_term(token, scopes, match)
        elif token != 'EOF':
            # The operand is a single term (a 'word' or a 'field:value' pair).
            self.parse_term(token, scopes, match)

        self.parse_closebracket(scopes, match)

    def parse_not(self, scopes, match):
        open_scope(scopes, Not())
        self.add_logical_scope(scopes, match)

    def parse_openbracket(self, scopes, match):
        open_scope(scopes, Group())

    def parse_closebracket(self, scopes, match):
        # Leave the current group.
        while type(scopes[-1]).__name__ != Group.__name__ and not scopes[-1].is_root:
            scopes.pop()
        if not scopes[-1].is_root:
            scopes.pop()

        # Auto-leave the parent scope (if necessary).
        close_scope(scopes)

    def parse(self, query):
        self._reset()
        self.input = query.strip()
        result = Group(is_root=True)
        scopes = [result]
        token, match = self._get_next_token()

        while token != 'EOF':
            self.parse_term(token, scopes, match)
            token, match = self._get_next_token()

        return result.optimize()
