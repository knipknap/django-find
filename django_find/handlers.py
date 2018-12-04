from django.db import models

class FieldHandler(object):
    """
    Abstract base type for all field handlers.

    A field handler is an object that you can use to define custom
    behavior when searching a field of a model.

    You might want to use a field handler if you are using a custom
    model field, or if your query contains information that
    requires client-side processing before being passed to
    the database.
    """
    db_type = None

    @classmethod
    def handles(cls, model, field):
        raise NotImplemented

    @classmethod
    def prepare(cls, value):
        return value

class StrFieldHandler(FieldHandler):
    db_type = 'STR'

    @classmethod
    def handles(cls, model, field):
        return isinstance(field, (models.CharField, models.TextField))

class LowerCaseStrFieldHandler(StrFieldHandler):
    db_type = 'LCSTR'

class IPAddressFieldHandler(LowerCaseStrFieldHandler):
    @classmethod
    def handles(cls, model, field):
        return isinstance(field, models.GenericIPAddressField)

class BooleanFieldHandler(FieldHandler):
    db_type = 'BOOL'

    @classmethod
    def handles(cls, model, field):
        return isinstance(field, models.BooleanField)

class IntegerFieldHandler(FieldHandler):
    db_type = 'INT'

    @classmethod
    def handles(cls, model, field):
        return isinstance(field, (models.IntegerField, models.AutoField))

class DateFieldHandler(FieldHandler):
    db_type = 'DATE'

    @classmethod
    def handles(cls, model, field):
        return isinstance(field, models.DateField)

class DateTimeFieldHandler(FieldHandler):
    db_type = 'DATETIME'

    @classmethod
    def handles(cls, model, field):
        return isinstance(field, models.DateTimeField)

type_registry = [
        LowerCaseStrFieldHandler,
        IPAddressFieldHandler,
        BooleanFieldHandler,
        IntegerFieldHandler,
        DateTimeFieldHandler,
        DateFieldHandler,
]
