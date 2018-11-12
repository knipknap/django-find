"""
This module contains the Searchable mixin, the main public API of
django-find.
"""
from __future__ import absolute_import, print_function
from collections import OrderedDict
from django.db import models
from .parsers.query import QueryParser
from .parsers.json import JSONParser
from .serializers.django import DjangoSerializer
from .refs import get_subclasses, get_object_vector_to, get_object_vector_for
from .rawquery import PaginatedRawQuerySet
from .model_helpers import sql_from_dom

type_map = (
        (models.CharField, 'LCSTR'),
        (models.TextField, 'LCSTR'),
        (models.GenericIPAddressField, 'LCSTR'),
        (models.BooleanField, 'BOOL'),
        (models.IntegerField, 'INT'),
        (models.AutoField, 'INT'),
)

class Searchable(object):
    """
    This class is a mixin for Django models that provides methods for
    searching the model using query strings and other tools.
    """

    searchable_labels = {} # Override the verbose_name for the given aliases
    searchable = () # Contains two-tuples, mapping aliases to Django selectors

    @classmethod
    def get_default_searchable(cls):
        return OrderedDict((f.name, f.name) for f in cls._meta.get_fields()
                           if not f.auto_created)

    @classmethod
    def get_searchable(cls):
        result = cls.get_default_searchable()
        if hasattr(cls, 'searchable'):
            result.update(OrderedDict(cls.searchable))
        return tuple(i for i in result.items() if i[1])

    @classmethod
    def get_caption_from_selector(cls, selector):
        caption = cls.searchable_labels.get(selector)
        if caption:
            return caption
        field = cls.get_field_from_selector(selector)[1]
        if hasattr(field, 'verbose_name'):
            return field.verbose_name
        return field.name.capitalize()

    @classmethod
    def get_field_type_from_field(cls, field):
        for field_model, typename in type_map:
            if isinstance(field, field_model):
                return typename
        raise TypeError('field {}.{} is of type {}, which is unsupported'.format(
            cls.__name__,
            field.name,
            type(field)))

    @classmethod
    def get_aliases(cls):
        """
        Returns a list of the aliases, that is, the names of the
        fields that can be used in a query.
        """
        return list(OrderedDict(cls.get_searchable()).keys())

    @classmethod
    def get_fullnames(cls):
        """
        Like get_aliases(), but returns the aliases prefixed by the class
        name.
        """
        aliases = cls.get_aliases()
        return [cls.__name__+'.'+alias for alias in aliases]

    @classmethod
    def table_headers(cls):
        selectors = set()
        result = []
        for item in cls.get_searchable():
            selector = item[1]
            if selector in selectors:
                continue
            selectors.add(selector)
            result.append(cls.get_caption_from_selector(selector))
        return result

    @classmethod
    def get_field_from_selector(cls, selector):
        """
        Given a django selector, e.g. device__metadata__name, this returns the class
        and the Django field of the model, as returned by Model._meta.get_field().
        Example::

            device__metadata__name -> (SeedDevice, SeeDevice.name)
        """
        if not '__' in selector:
            return cls, cls._meta.get_field(selector)

        model = cls
        while '__' in selector:
            model_name, selector = selector.split('__', 1)
            model = model._meta.get_field(model_name).rel.to

        return model, model._meta.get_field(selector)

    @classmethod
    def get_field_type_from_alias(cls, alias):
        """
        Given an alias, e.g. 'host', 'name',
        this function returns the target type, e.g.::

            'LCSTR'

        @type name: str
        @param name: e.g. 'address', or 'name'
        """
        selector = cls.get_selector_from_alias(alias)
        field = cls.get_field_from_selector(selector)[1]
        return cls.get_field_type_from_field(field)

    @classmethod
    def get_field_type_from_fullname(cls, fullname):
        """
        Given a fullname, e.g. 'Device.host', 'Author.name',
        this function returns the target type, e.g.::

            'LCSTR'

        @type name: str
        @param name: e.g. 'address', or 'name'
        """
        thecls, alias = cls.get_class_from_fullname(fullname)
        return thecls.get_field_type_from_alias(alias)

    @classmethod
    def get_selector_from_alias(cls, alias):
        """
        Given alias (not a fullname), this function returns the
        selector in the following form::

            component__device__host

        @type name: str
        @param name: e.g. 'address', or 'name'
        """
        return dict(cls.get_searchable())[alias]

    @classmethod
    def get_object_vector_to(cls, search_cls):
        return get_object_vector_to(cls, search_cls, Searchable)

    @classmethod
    def get_object_vector_for(cls, search_cls_list):
        return get_object_vector_for(cls, search_cls_list, Searchable)

    @classmethod
    def get_class_from_fullname(cls, fullname):
        """
        Given a name in the format "Model.hostname", this
        function returns a tuple, where the first element is the Model
        class, and the second is the field name "hostname".

        The Model class must inherit from Searchable to be found.
        """
        if '.' not in fullname:
            raise AttributeError('class name is required, format should be "Class.alias"')

        # Search the class.
        clsname, alias = fullname.split('.', 1)
        thecls = None
        for subclass in get_subclasses(Searchable):
            if subclass.__module__ == '__fake__':
                # Skip Django-internal models
                continue
            if subclass.__name__ == clsname:
                thecls = subclass
                break
        if thecls is None:
            raise KeyError('no such class: ', clsname)

        return subclass, alias

    @classmethod
    def get_selector_from_fullname(cls, fullname):
        """
        Given a name in the form 'Unit.hostname', this function returns
        a Django selector that can be used for filtering.
        Example (assuming the models are Book and Author)::

            Book.get_selector_from_fullname('Author.birthdate')
            # returns 'author__birthdate'

        Example for the models Blog, Entry, Comment::

            Blog.get_selector_from_fullname('Comment.author')
            # returns 'entry__comment__author'

        @type name: str
        @param name: The field to select for
        @rtype: str
        @return: The Django selector
        """
        # Get the target class and attribute by parsing the name.
        target_cls, alias = cls.get_class_from_fullname(fullname)
        selector = target_cls.get_selector_from_alias(alias)
        if target_cls == cls:
            return selector

        # Prefix the target by the class names.
        path_list = get_object_vector_to(cls, target_cls, Searchable)
        path = path_list[0]
        prefix = ''
        for thecls in path[1:]:
            prefix += thecls.__name__.lower() + '__'
            if thecls == target_cls:
                return prefix+selector

        raise Exception('BUG: class %s not in path %s' % (target_cls, path))

    @classmethod
    def get_primary_class_from_fullnames(cls, fullnames):
        if not fullnames:
            return cls
        return cls.get_class_from_fullname(fullnames[0])[0]

    @classmethod
    def by_fullnames(cls, fullnames):
        """
        Returns a unfiltered values_list() of all given field names.
        """
        selectors = [cls.get_selector_from_fullname(f) for f in fullnames]
        primary_cls = cls.get_primary_class_from_fullnames(fullnames)
        return primary_cls.objects.values_list(*selectors)

    @classmethod
    def dom_from_query(cls, query):
        fields = {}
        aliases = cls.get_aliases()
        for alias in aliases:
            fields[alias] = cls.__name__+'.'+alias
        query_parser = QueryParser(fields, aliases)
        return query_parser.parse(query)

    @classmethod
    def q_from_query(cls, query):
        """
        Returns a Q-Object for the given query.
        """
        dom = cls.dom_from_query(query)
        serializer = DjangoSerializer(cls)
        return dom.serialize(serializer)

    @classmethod
    def by_query(cls, query):
        return cls.objects.filter(cls.q_from_query(query))

    @classmethod
    def sql_from_query(cls, query, mode='SELECT', fullnames=None, extra_model=None):
        """
        Returns an SQL statement for the given query.
        """
        dom = cls.dom_from_query(query)
        return sql_from_dom(cls, dom,
                            mode=mode,
                            fullnames=fullnames,
                            extra_model=extra_model)

    @classmethod
    def by_query_raw(cls, query, mode='SELECT', fullnames=None, extra_model=None):
        """
        Returns a PaginatedRawQuerySet for the given query.
        """
        sql, args, fields = cls.sql_from_query(query,
                                               mode=mode,
                                               fullnames=fullnames,
                                               extra_model=extra_model)
        return PaginatedRawQuerySet(sql, args), fields

    @classmethod
    def sql_from_json(cls, json_string, mode='SELECT', extra_model=None):
        dom = JSONParser().parse(json_string)
        return sql_from_dom(cls, dom, extra_model=extra_model)

    @classmethod
    def by_json_raw(cls, json_string, extra_model=None):
        sql, args, fields = cls.sql_from_json(json_string,
                                              extra_model=extra_model)
        return PaginatedRawQuerySet(sql, args), fields
