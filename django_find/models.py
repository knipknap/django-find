"""
This module contains the Searchable mixin, the main public API of
django-find.
"""
from collections import OrderedDict
from django.apps import AppConfig
from django.db import models
from .parsers.query import QueryParser
from .parsers.json import JSONParser
from .serializers.django import DjangoSerializer
from .refs import get_subclasses, get_object_vector_to, get_object_vector_for
from .rawquery import PaginatedRawQuerySet
from .model_helpers import sql_from_dom
from .handlers import type_registry

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
    def get_field_handler_from_field(cls, field):
        if isinstance(field, models.ForeignKey):
            field = field.target_field
        for handler in type_registry:
            if handler.handles(cls, field):
                return handler
        msg = 'field {}.{} is of type {}'.format(cls.get_classname(),
                                                 field.name,
                                                 type(field))
        raise TypeError(msg + ', which has no field handler. Consider adding a '
                      + 'django_find.handlers.FieldHandler to the '
                      + 'django_find.handlers.type_registry. See the docs for'
                      + 'more information')

    @classmethod
    def get_aliases(cls):
        """
        Returns a list of the aliases, that is, the names of the
        fields that can be used in a query.
        """
        return list(OrderedDict(cls.get_searchable()).keys())
    
    @classmethod
    def get_classname(cls):
        """
        Returns a string for the classes name including the modules path.
        """
        return "{}.{}".format(cls.__module__, cls.__name__)

    @classmethod
    def get_fullnames(cls, unique=False):
        """
        Like get_aliases(), but returns the aliases prefixed by the class
        name.
        """
        if unique:
            selectors = set()
            result = []
            for item in cls.get_searchable():
                selector = item[1]
                if selector in selectors:
                    continue
                selectors.add(selector)
                result.append(cls.get_classname()+'.'+item[0])
            return result
        else:
            aliases = cls.get_aliases()
            return [cls.get_classname()+'.'+alias for alias in aliases]

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
            model = model._meta.get_field(model_name).remote_field.model

        return model, model._meta.get_field(selector)

    @classmethod
    def get_field_handler_from_alias(cls, alias):
        """
        Given an alias, e.g. 'host', 'name',
        this function returns the handler.FieldHandler.

        @type name: str
        @param name: e.g. 'address', or 'name'
        """
        selector = cls.get_selector_from_alias(alias)
        field = cls.get_field_from_selector(selector)[1]
        return cls.get_field_handler_from_field(field)

    @classmethod
    def get_field_handler_from_fullname(cls, fullname):
        """
        Given a fullname, e.g. 'Device.host', 'Author.name',
        this function returns the handler.FieldHandler.

        @type name: str
        @param name: e.g. 'address', or 'name'
        """
        thecls, alias = cls.get_class_from_fullname(fullname)
        return thecls.get_field_handler_from_alias(alias)

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
            if subclass.get_classname() == clsname:
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
            prefix += thecls.get_classname().lower() + '__'
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
    def dom_from_query(cls, query, aliases=None):
        if not aliases:
            aliases = cls.get_aliases()
        fields = {}
        for alias in aliases:
            fields[alias] = cls.get_classname()+'.'+alias
        query_parser = QueryParser(fields, aliases)
        return query_parser.parse(query)

    @classmethod
    def q_from_query(cls, query, aliases=None):
        """
        Returns a Q-Object for the given query.
        """
        dom = cls.dom_from_query(query, aliases)
        serializer = DjangoSerializer(cls)
        return dom.serialize(serializer)

    @classmethod
    def by_query(cls, query, aliases=None):
        return cls.objects.filter(cls.q_from_query(query, aliases))

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
        return PaginatedRawQuerySet(cls, sql, args), fields

    @classmethod
    def sql_from_json(cls, json_string, mode='SELECT', extra_model=None):
        dom = JSONParser().parse(json_string)
        return sql_from_dom(cls, dom, extra_model=extra_model)

    @classmethod
    def by_json_raw(cls, json_string, extra_model=None):
        sql, args, fields = cls.sql_from_json(json_string,
                                              extra_model=extra_model)
        return PaginatedRawQuerySet(cls, sql, args), fields
