from django.db import connection

SQL_MAXINT=9223372036854775807 # SQLite maxint

def assert_positive_slice(slc):
    if (slc.start is not None and slc.start < 0) or \
       (slc.stop is not None and slc.stop < 0):
       raise IndexError("Negative indexing is not supported")

class PaginatedRawQuerySet(object):
    def __init__(self, model, raw_query, args=None, limit=None, offset=None):
        self.model = model
        self.raw_query = raw_query
        self.args = args if args else []
        self.limit = limit
        self.offset = offset or 0
        self.result_cache = None
        self.count_cache = None

    def __copy__(self):
        return self.__class__(self.model,
                              self.raw_query,
                              self.args,
                              limit=self.limit,
                              offset=self.offset)

    def _getslice(self, slc):
        assert_positive_slice(slc)
        qs = self.__copy__()
        qs.offset = slc.start or 0
        qs.limit = None if slc.stop is None else (slc.stop-qs.offset)
        return qs

    def _getindex(self, idx):
        if idx < 0:
            raise IndexError("Negative indexing is not supported")
        qs = self.__copy__()
        qs.offset = self.offset+idx if self.offset else idx
        qs.limit = 1
        return list(qs)[idx]

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        """
        if isinstance(k, slice):
            return self._getslice(k)
        if isinstance(k, int):
            return self._getindex(k)
        raise TypeError

    @property
    def query(self):
        query = self.raw_query
        if self.limit is None:
            query += ' LIMIT '+str(SQL_MAXINT-self.offset)+' OFFSET '+str(int(self.offset))
        else:
            query += ' LIMIT '+str(int(self.limit))+' OFFSET '+str(int(self.offset))
        return query

    def __iter__(self):
        if self.result_cache is None:
            with connection.cursor() as cursor:
                cursor.execute(self.query, self.args)
                self.result_cache = cursor.fetchall()
        return iter(self.result_cache)

    def __len__(self):
        if self.count_cache is not None:
            return self.count_cache
        query = 'SELECT COUNT(*) FROM (' + self.query + ') c'
        with connection.cursor() as cursor:
            cursor.execute(query, self.args)
            row = cursor.fetchone()
            self.count_cache = int(row[0])
        return self.count_cache

    count = property(__len__) # For better compatibility to Django's QuerySet
