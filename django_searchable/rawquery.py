from django.db import connection

class PaginatedRawQuerySet(object):
    def __init__(self, raw_query, args, limit=None, offset=None):
        self.raw_query = raw_query
        self.args = args
        self.limit = limit
        self.offset = offset
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
        if not isinstance(k, (slice, int,)):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0)) or
                (isinstance(k, slice) and (k.start is None or k.start >= 0) and
                 (k.stop is None or k.stop >= 0))), \
            "Negative indexing is not supported."

        if isinstance(k, slice):
            qs = self.__copy__()
            qs.offset = k.start or 0
            qs.limit = k.stop-k.start or None
            return qs

        qs = self.__copy__()
        qs.offset = self.offset+k if self.offset else k
        qs.limit = 1
        return list(qs)[k]

    @property
    def query(self):
        query = self.raw_query
        if self.limit is not None:
            query += ' LIMIT '+str(int(self.limit))
        if self.offset is not None:
            query += ' OFFSET '+str(int(self.offset))
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
