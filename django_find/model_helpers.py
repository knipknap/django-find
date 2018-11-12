from .serializers.sql import SQLSerializer

def sql_from_dom(cls, dom, mode='SELECT', fullnames=None, extra_model=None):
    if not fullnames:
        fullnames = dom.get_term_names()
    if not fullnames:
        return 'SELECT * FROM (SELECT NULL) tbl WHERE 0', [], [] # Empty set
    primary_cls = cls.get_primary_class_from_fullnames(fullnames)
    serializer = SQLSerializer(primary_cls,
                               mode=mode,
                               fullnames=fullnames,
                               extra_model=extra_model)
    sql, args = dom.serialize(serializer)
    return sql, args, fullnames
