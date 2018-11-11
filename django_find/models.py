from __future__ import absolute_import, print_function
from collections import OrderedDict
from django.db import models
from .parsers.query import QueryParser
from .parsers.json import JSONParser
from .serializers.django import DjangoSerializer
from .serializers.sql import SQLSerializer
from .refs import get_subclasses, get_object_vector_to, get_object_vector_for
from .rawquery import PaginatedRawQuerySet

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

class Searchable(object):
    """
    This class is a mixin for Django models that provides methods for
    searching the model using query strings and other tools.
    """

    searchable_labels = {}

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
    def get_caption_from_target_name(cls, target_name):
        caption = cls.searchable_labels.get(target_name)
        if caption:
            return caption
        field = cls.get_field_from_target_name(target_name)[1]
        if hasattr(field, 'verbose_name'):
            return field.verbose_name
        return field.name.capitalize()

    @classmethod
    def get_target_type_from_field(cls, field):
        if hasattr(cls, 'search_aliases') and field.name in cls.search_aliases:
            selector = cls.search_aliases[field.name]
            field = cls.get_field_from_target_name(selector)[1]
        elif field.auto_created and not field.one_to_one:
            #print("REVERSE", field.name, field)
            return None

        #print(field.name, type(field))
        if field.many_to_one:
            #print("BEFORE", field.name, field, dir(field))
            field = field.target_field
            #print("AFTER", field.name, field, type(field))
        elif field.many_to_many:
            #print("BEFORE", field.name, field, dir(field))
            field = field.target_field
            #print("AFTER", field.name, field, type(field))
        elif field.is_relation:
            return None
            field = field.get_related_field()

        if isinstance(field, (models.CharField, models.GenericIPAddressField)):
            return 'LCSTR'
        elif isinstance(field, models.BooleanField):
            return 'BOOL'
        elif isinstance(field, models.IntegerField):
            return 'INT'
        elif isinstance(field, models.AutoField):
            return 'INT'
            #print("SKIPPING", field.name, type(field))
            return None
        else:
            return None
            raise TypeError('fields of type {} unsupported'.format(type(field)))

    @classmethod
    def get_field_names(cls):
        return OrderedDict(cls.get_searchable()).keys()

    @classmethod
    def get_full_field_names(cls):
        """
        Like get_field_names(), but returns the names prefixed by the class name.
        """
        fields = cls.get_field_names()
        return [cls.__name__+'.'+key for key in fields]

    @classmethod
    def table_headers(cls):
        targets = set()
        result = []
        for item in cls.get_searchable():
            target = item[1]
            if target in targets:
                continue
            targets.add(target)
            result.append(cls.get_caption_from_target_name(target))
        return result

    @classmethod
    def search_criteria(cls):
        targets = set()
        result = []
        for alias, target_name in cls.get_searchable():
            if target_name in targets:
                continue
            targets.add(target_name)
            caption = cls.get_caption_from_target_name(target_name)
            result.append((caption, alias))
        return result

    @classmethod
    def get_field_from_target_name(cls, name):
        """
        Given the target name, e.g. device__metadata__name, this returns the class
        and the Django field of the model, as returned by Model._meta.get_field().
        Example::

            device__metadata__name -> (SeedDevice, SeeDevice.name)
        """
        if not '__' in name:
            return cls, cls._meta.get_field(name)

        model = cls
        while '__' in name:
            model_name, name = name.split('__', 1)
            model = model._meta.get_field(model_name).rel.to

        return model, model._meta.get_field(name)

    @classmethod
    def get_target_from_name(cls, name):
        """
        Given a field name or alias, e.g. 'host', 'address', 'hostname',
        this function returns the target, e.g.::

            LCSTR:component__device__host

        @type name: str
        @param name: e.g. 'address', or 'name'
        """
        target_name = cls.get_target_name_from_name(name)
        field = cls.get_field_from_target_name(target_name)[1]
        target_type = cls.get_target_type_from_field(field)
        return target_type, target_name

    @classmethod
    def get_target_name_from_name(cls, name):
        """
        Like get_target_from_name(), but returns the following form::

            component__device__host

        @type name: str
        @param name: e.g. 'address', or 'name'
        """
        return dict(cls.get_searchable())[name]

    @classmethod
    def get_object_vector_to(cls, search_cls):
        return get_object_vector_to(cls, search_cls, Searchable)

    @classmethod
    def get_object_vector_for(cls, search_cls_list):
        return get_object_vector_for(cls, search_cls_list, Searchable)

    @classmethod
    def get_class_from_field_name(cls, name):
        """
        Given a name in the format "Model.hostname", this
        function returns a tuple, where the first element is the Model
        class, and the second is the field name "hostname".

        The Model class must inherit from Searchable to be found.
        """
        if '.' in name:
            clsname, field_name = name.split('.', 1)
        else:
            raise AttributeError('class name is required, format should be "Class.alias"')

        # Search the class.
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

        return subclass, field_name

    @classmethod
    def get_selector_from_field_name(cls, name):
        """
        Given a name in the form 'Unit.hostname', this function returns
        a Django selector that can be used for filtering.
        Example (assuming the models are Book and Author)::

            Book.get_selector_from_field_name('Author.birthdate')
            # returns 'author__birthdate'

        Example for the models Blog, Entry, Comment::

            Blog.get_selector_from_field_name('Comment.author')
            # returns 'entry__comment__author'

        @type name: str
        @param name: The field to select for
        @rtype: str
        @return: The Django selector
        """
        # Get the target class and attribute by parsing the name.
        target_cls, field_name = cls.get_class_from_field_name(name)
        target = target_cls.get_target_name_from_name(field_name)
        if target_cls == cls:
            return target

        # Prefix the target by the class names.
        path_list = get_object_vector_to(cls, target_cls, Searchable)
        path = path_list[0]
        prefix = ''
        for thecls in path[1:]:
            prefix += thecls.__name__.lower() + '__'
            if thecls == target_cls:
                return prefix+target

        raise Exception('BUG: class %s not in path %s' % (target_cls, path))

    @classmethod
    def get_primary_class_from_field_names(cls, field_names):
        if not field_names:
            return cls
        first_field_name = field_names[0]
        primary_cls, _ = cls.get_class_from_field_name(first_field_name)
        return primary_cls

    @classmethod
    def by_field_names(cls, field_names):
        """
        Returns a unfiltered values_list() of all given field names.
        """
        selectors = [cls.get_selector_from_field_name(f) for f in field_names]
        primary_cls = cls.get_primary_class_from_field_names(field_names)
        return primary_cls.objects.values_list(*selectors)

    @classmethod
    def dom_from_query(cls, query):
        fields = {}
        for alias, target_name in cls.get_searchable():
            fields[alias] = cls.__name__+'.'+alias
        default_fields = cls.get_field_names()
        query_parser = QueryParser(fields, default_fields)
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
    def sql_from_query(cls, query, mode='SELECT', field_names=None, extra_model=None):
        """
        Returns an SQL statement for the given query.
        """
        dom = cls.dom_from_query(query)
        return sql_from_dom(cls, dom,
                            mode=mode,
                            field_names=field_names,
                            extra_model=extra_model)

    @classmethod
    def by_query_raw(cls, query, mode='SELECT', field_names=None, extra_model=None):
        """
        Returns a PaginatedRawQuerySet for the given query.
        """
        sql, args, fields = cls.sql_from_query(query,
                                               mode=mode,
                                               field_names=field_names,
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
