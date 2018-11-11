from .serializers.sql import SQLSerializer

def sql_from_dom(cls, dom, mode='SELECT', field_names=None, extra_model=None):
    if not field_names:
        field_names = dom.get_term_names()
    if not field_names:
        return 'SELECT * FROM (SELECT NULL) tbl WHERE 0', [], [] # Empty set
    primary_cls = cls.get_primary_class_from_field_names(field_names)
    serializer = SQLSerializer(primary_cls,
                               mode=mode,
                               field_names=field_names,
                               extra_model=extra_model)
    sql, args = dom.serialize(serializer)
    return sql, args, field_names
