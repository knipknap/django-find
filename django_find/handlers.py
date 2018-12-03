from django.db import models

class Handler(object):
    db_type = 'LCSTR'

    def __init__(self, value):
        self.value = value

    @classmethod
    def handles(cls, field):
        raise NotImplemented

    def prepare(self):
        return self.value

class StrHandler(Handler):
    @classmethod
    def handles(cls, field):
        return isinstance(field, (models.CharField, models.TextField))

class LowerCaseStrHandler(StrHandler):
    def prepare(self):
        return self.value.lower()

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
