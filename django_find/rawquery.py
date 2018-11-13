from django.db import connection

SQL_MAXINT=9223372036854775807 # SQLite maxint

class PaginatedRawQuerySet(object):
    def __init__(self, raw_query, args=None, limit=None, offset=None):
        self.raw_query = raw_query
        self.args = args if args else []
        self.limit = limit
        self.offset = offset or 0
        self.result_cache = None
        self.count_cache = None

    def __copy__(self):
        return self.__class__(self.raw_query, self.args,
                              limit=self.limit,
                              offset=self.offset)

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        """
        if isinstance(k, slice):
            if (k.start is not None and k.start < 0) or \
               (k.stop is not None and k.stop < 0):
               raise IndexError("Negative indexing is not supported")
        elif isinstance(k, int):
            if k < 0:
                raise IndexError("Negative indexing is not supported")
        else:
            raise TypeError

        if isinstance(k, slice):
            qs = self.__copy__()
            qs.offset = k.start or 0
            qs.limit = (k.stop-qs.offset) if k.stop is not None else None
            return qs

        qs = self.__copy__()
        qs.offset = self.offset+k if self.offset else k
        qs.limit = 1
        return list(qs)[k]

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
