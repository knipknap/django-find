from __future__ import absolute_import, print_function, unicode_literals
from builtins import str
from MySQLdb import escape_string
from ..refs import get_join_for
from .serializer import Serializer

def _mkcol(tbl, name):
    return tbl+'.'+name+' '+tbl+'_'+name

class SQLSerializer(Serializer):
    def __init__(self, model, mode='SELECT', field_names=None, extra_model=None):
        modes = 'SELECT', 'WHERE'
        if mode not in modes:
            raise AttributeError('invalid mode: {}. Must be one of {}'.format(mode, modes))
        Serializer.__init__(self)
        self.model = model
        self.mode = mode
        self.field_names = field_names
        self.extra_model = extra_model

    def _create_db_column_list(self, dom):
        field_names = self.field_names if self.field_names else dom.get_term_names()
        result = []
        for field_name in field_names:
            model, name = self.model.get_class_from_field_name(field_name)
            target_name = model.get_target_name_from_name(name)
            target_model, field = model.get_field_from_target_name(target_name)
            result.append((field_name, target_model, target_model._meta.db_table, field.column))
        return result

    def logical_root_group(self, root_group, terms):
        fields = self._create_db_column_list(root_group)

        # Create the SELECT part of the query.
        args = []
        if self.mode == 'SELECT':
            # Create the "SELECT DISTINCT table1.col1, table2.col2, ..."
            # part of the SQL.
            select = 'SELECT DISTINCT '+_mkcol(fields[0][2], fields[0][3])
            for field_name, target_model, table, column in fields[1:]:
                select += ', '+_mkcol(table, column)

            # Find the best way to join the tables.
            target_models = [r[1] for r in fields]
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

            select += ' WHERE '
        else:
            select = ''

        where = (' AND '.join(terms) if terms else '1')
        if where.startswith('(') and where.endswith(')'):
            select += where
        else:
            select += '('+where+')'
        return select, args

    def logical_group(self, terms):
        if not terms:
            return ''
        return ' AND '.join(terms)

    def logical_and(self, terms):
        if not terms:
            return '()'
        return '(' + self.logical_group(terms) + ')'

    def logical_or(self, terms):
        if not terms:
            return ''
        return '(' + ' OR '.join(terms) + ')'

    def logical_not(self, terms):
        if not terms:
            return ''
        if len(terms) == 1:
            return 'NOT(' + terms[0] + ')'
        return 'NOT ' + self.logical_and(terms)

    def term(self, field_name, operator, data):
        model, name = self.model.get_class_from_field_name(field_name)
        target_type, target_name = model.get_target_from_name(name)
        target_model, field = model.get_field_from_target_name(target_name)
        db_column = target_model._meta.db_table + '.' + field.column

        # Handle case-insensitive queries.
        if target_type == 'LCSTR':
            data = data.lower()
            name = 'LOWER(' + db_column + ')'

        # Generate the LIKE or "=" statement.
        if operator == 'equals':
            result = db_column+"='{}'"
        elif operator == 'startswith':
            result = db_column+" LIKE '{}%%'"
        elif operator == 'endswith':
            result = db_column+" LIKE '%%{}'"
        elif operator == 'contains':
            result = db_column+" LIKE '%%{}%%'"
        elif operator == 'regex':
            result = db_column+" REGEXP '%%{}%%'"
        elif operator == 'any':
            result = '1'
        else:
            raise Exception('unsupported operator:' + str(operator))

        # Yes, I would prefer to use a prepared statement, but collecting arguments
        # and passing them back along the string everywhere would be awful design,
        # and if you prefer that, you are a bad software developer.
        # (Also, I didn't find any API from Django to generate a prepared statement
        # without already executing it, e.g. django.db.connection.execute())
        return result.format(escape_string(data).decode('utf-8'))
