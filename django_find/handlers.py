from django.db import models

class Handler(object):
    db_type = None

    @classmethod
    def handles(cls, field):
        raise NotImplemented

    @classmethod
    def prepare(cls, value):
        return value

class StrHandler(Handler):
    db_type = 'STR'

    @classmethod
    def handles(cls, field):
        return isinstance(field, (models.CharField, models.TextField))

class LowerCaseStrHandler(StrHandler):
    db_type = 'LCSTR'

class IPAddressHandler(LowerCaseStrHandler):
    @classmethod
    def handles(cls, field):
        return isinstance(field, models.GenericIPAddressField)

class BooleanHandler(Handler):
    db_type = 'BOOL'

    @classmethod
    def handles(cls, field):
        return isinstance(field, models.BooleanField)

class IntegerHandler(Handler):
    db_type = 'INT'

    @classmethod
    def handles(cls, field):
        return isinstance(field, (models.IntegerField, models.AutoField))

class DateHandler(Handler):
    db_type = 'DATE'

    @classmethod
    def handles(cls, field):
        return isinstance(field, models.DateField)

class DateTimeHandler(Handler):
    db_type = 'DATETIME'

    @classmethod
    def handles(cls, field):
        return isinstance(field, models.DateTimeField)

type_registry = [
        LowerCaseStrHandler,
        IPAddressHandler,
        BooleanHandler,
        IntegerHandler,
        DateTimeHandler,
        DateHandler,
]
