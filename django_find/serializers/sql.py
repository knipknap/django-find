from __future__ import absolute_import, print_function, unicode_literals
from builtins import str
from MySQLdb import escape_string
from ..refs import get_join_for
from .serializer import Serializer
from .util import parse_date, parse_datetime

int_op_map = {'equals': 'equals',
              'contains': 'equals',
              'startswith': 'gte',
              'endswith': 'lte'}

str_op_map = {'gt': 'startswith',
              'gte': 'startswith',
              'lt': 'endswith',
              'lte': 'endswith'}

date_op_map = {'contains': 'equals',
               'startswith': 'gte',
               'endswith': 'lte'}

operator_map = {
    'equals': "='{}'",
    'iequals': " LIKE '{}'",
    'lt': "<'{}'",
    'lte': "<='{}'",
    'gt': ">'{}'",
    'gte': ">='{}'",
    'startswith': " LIKE '{}%%'",
    'endswith': " LIKE '%%{}'",
    'contains': " LIKE '%%{}%%'",
    'regex': " REGEXP '%%{}%%'"}

def _mkcol(tbl, name):
    return tbl+'.'+name+' '+tbl+'_'+name

def _mk_condition(db_column, operator, data):
    op = operator_map.get(operator)
    if not op:
        raise Exception('unsupported operator:' + str(operator))

    # I would prefer to use a prepared statement, but collecting arguments
    # and passing them back along the string everywhere would be awful design.
    # (Also, I didn't find any API from Django to generate a prepared statement
    # without already executing it, e.g. django.db.connection.execute())
    if isinstance(data, int):
        return db_column+op.format(data)
    return db_column+op.format(escape_string(data).decode('utf-8'))

class SQLSerializer(Serializer):
    def __init__(self, model, mode='SELECT', fullnames=None, extra_model=None):
        modes = 'SELECT', 'WHERE'
        if mode not in modes:
            raise AttributeError('invalid mode: {}. Must be one of {}'.format(mode, modes))
        Serializer.__init__(self)
        self.model = model
        self.mode = mode
        self.fullnames = fullnames
        self.extra_model = extra_model

    def _create_db_column_list(self, dom):
        fullnames = self.fullnames if self.fullnames else dom.get_term_names()
        result = []
        for fullname in fullnames:
            model, alias = self.model.get_class_from_fullname(fullname)
            selector = model.get_selector_from_alias(alias)
            target_model, field = model.get_field_from_selector(selector)
            result.append((target_model, target_model._meta.db_table, field.column))
        return result

    def _create_select(self, fields):
        # Create the "SELECT DISTINCT table1.col1, table2.col2, ..."
        # part of the SQL.
        select = 'SELECT DISTINCT '+_mkcol(fields[0][1], fields[0][2])
        for target_model, table, column in fields[1:]:
            select += ', '+_mkcol(table, column)

        # Find the best way to join the tables.
        target_models = [r[0] for r in fields]
        if self.extra_model:
            target_models.append(self.extra_model)
        vector = self.model.get_object_vector_for(target_models)
        join_path = get_join_for(vector)

        # Create the "table1 LEFT JOIN table2 ON table1.col1=table2.col1"
        # part of the SQL.
        select += ' FROM '+join_path[0][0]
        for table, left, right in join_path[1:]:
            select += ' LEFT JOIN {} ON {}={}'.format(table,
                                                      table+'.'+left,
                                                      right)
        return select

    def logical_root_group(self, root_group, terms):
        fields = self._create_db_column_list(root_group)

        # Create the SELECT part of the query.
        if self.mode == 'SELECT':
            select = self._create_select(fields)+' WHERE '
        else:
            select = ''

        where = (' AND '.join(terms) if terms else '1')
        if where.startswith('(') and where.endswith(')'):
            select += where
        else:
            select += '('+where+')'
        return select, []

    def logical_group(self, terms):
        terms = [t for t in terms if t]
        if not terms:
            return ''
        return ' AND '.join(terms)

    def logical_and(self, terms):
        terms = [t for t in terms if t]
        if not terms:
            return '()'
        return '(' + self.logical_group(terms) + ')'

    def logical_or(self, terms):
        terms = [t for t in terms if t]
        if not terms:
            return ''
        return '(' + ' OR '.join(terms) + ')'

    def logical_not(self, terms):
        if not terms:
            return ''
        if len(terms) == 1:
            return 'NOT(' + terms[0] + ')'
        return 'NOT ' + self.logical_and(terms)

    def boolean_term(self, db_column, operator, data):
        value = 'TRUE' if data.lower() == 'true' else 'FALSE'
        return _mk_condition(db_column, operator, value)

    def int_term(self, db_column, operator, data):
        try:
            value = int(data)
        except ValueError:
            return '1'
        operator = int_op_map.get(operator, operator)
        return _mk_condition(db_column, operator, value)

    def str_term(self, db_column, operator, data):
        operator = str_op_map.get(operator, operator)
        return _mk_condition(db_column, operator, data)

    def lcstr_term(self, db_column, operator, data):
        operator = str_op_map.get(operator, operator)
        if operator == 'equals':
            operator = 'iequals'
        return _mk_condition(db_column, operator, data.lower())

    def date_datetime_common(self, db_column, operator, thedatetime):
        if not thedatetime:
            return ''
        operator = date_op_map.get(operator, operator)
        return _mk_condition(db_column, operator, thedatetime.isoformat())

    def date_term(self, db_column, operator, data):
        thedate = parse_date(data)
        return self.date_datetime_common(db_column, operator, thedate)

    def datetime_term(self, db_column, operator, data):
        thedatetime = parse_datetime(data)
        return self.date_datetime_common(db_column, operator, thedatetime)

    def term(self, term_name, operator, data):
        if operator == 'any':
            return '1'

        model, alias = self.model.get_class_from_fullname(term_name)
        selector = model.get_selector_from_alias(alias)
        target_model, field = model.get_field_from_selector(selector)
        db_column = target_model._meta.db_table + '.' + field.column
        handler = model.get_field_handler_from_alias(alias)

        type_map = {'BOOL': self.boolean_term,
                    'INT': self.int_term,
                    'STR': self.str_term,
                    'LCSTR': self.lcstr_term,
                    'DATE': self.date_term,
                    'DATETIME': self.datetime_term}

        func = type_map.get(handler.db_type)
        if not func:
            raise TypeError('unsupported field type: '+repr(field_type))
        return func(db_column, operator, handler.prepare(data))
