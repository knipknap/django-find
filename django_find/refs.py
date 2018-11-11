from copy import copy
from itertools import chain
from django.db import models
from django.db.models.fields.related import ManyToOneRel, ManyToManyRel

def get_subclasses(cls):
    """
    Recursively finds all subclasses of the current class.
    Like Python's __class__.__subclasses__(), but recursive.
    Returns a list containing all subclasses.

    @type cls: object
    @param cls: A Python class.
    @rtype: list(object)
    @return: A list containing all subclasses.
    """
    result = set()
    path = [cls]
    while path:
        parent = path.pop()
        for child in parent.__subclasses__():
            if not '.' in str(child):
                # In a multi inheritance scenario, __subclasses__()
                # also returns interim-classes that don't have all the
                # methods. With this hack, we skip them.
                continue
            if child not in result:
                result.add(child)
                path.append(child)
    return result

def child_classes(cls):
    """
    Returns all models that have a foreign key pointing to cls.
    """
    children = []
    for field in cls._meta.get_fields():
        if isinstance(field, (ManyToOneRel, ManyToManyRel)):
            children.append(field.related_model)
    return children

def parent_classes(cls):
    """
    Returns all models that are referenced by a foreign key of the
    given class.
    """
    parents = []
    for field in cls._meta.get_fields():
        if isinstance(field, (models.ForeignKey, models.ManyToManyField)):
            parents.append(field.rel.to)
    return parents

def get_field_to(cls, target_cls):
    for field in cls._meta.get_fields():
        if not isinstance(field, (models.ForeignKey, models.ManyToManyField)):
            continue
        if field.rel.to is target_cls:
            return field
    return None

def get_object_vector_to(cls, search_cls, subtype, avoid=None):
    """
    Returns a list of all possible paths to the given class.
    Only searches classes that are subtype of the given class.
    """
    # Does the name point to this class? Then we are done.
    if search_cls == cls:
        return [(cls,)]

    # Avoid endless recursion.
    if avoid is None:
        avoid = set()
    else:
        avoid = copy(avoid)
    avoid.add(cls)

    # So the name does not point to this class. Delegate the request to
    # each of our connected classes, collecting all possible paths.
    path_list = []
    for thecls in chain(child_classes(cls), parent_classes(cls)):
        if thecls in avoid:
            continue
        if subtype in thecls.__mro__:
            child_path_list = get_object_vector_to(thecls, search_cls, subtype, copy(avoid))
        elif thecls == search_cls:
            child_path_list = [(thecls,)]
        else:
            continue
        for path in child_path_list:
            path_list.append((cls,)+path)
    path_list.sort(key=len)
    return path_list

def yield_all_vectors(search_cls_list, subtype):
    """ 
    Yields all possible vectors between all given classes.
    """
    for target_cls in search_cls_list[:]:
        for thecls in search_cls_list:
            vectors = get_object_vector_to(thecls, target_cls, subtype)
            for vector in vectors:
                yield vector

def yield_matching_vectors(vectors, search_cls_list):
    """
    Yields all possible vectors that connect all of the given classes.
    The result is sorted by the position of the primary class, and
    the vector length.
    """
    for vector in vectors:
        for target_cls in search_cls_list:
            if target_cls not in vector:
                break
        else:
            yield vector

def sort_vectors_by_primary_cls(vectors, primary_cls):
    """
    Sort the vectors by the position of the primary class, and
    the vector length.
    """
    def sort_by_length_and_pos_of_primary_cls(vector):
        try:
            pos = vector.index(primary_cls)
        except ValueError:
            pos = 0
        return float('{}.{}'.format(pos, len(vector)))
    return sorted(vectors, key=sort_by_length_and_pos_of_primary_cls)

def get_object_vector_for(cls, search_cls_list, subtype, avoid=None):
    """
    Like get_object_vector_to(), but returns a single vector that reaches
    all of the given classes, if it exists.
    Only searches classes that are subtype of the given class.
    """
    vectors = list(yield_all_vectors(search_cls_list, subtype))
    matching = list(yield_matching_vectors(vectors, search_cls_list))
    if not matching:
        return None # No vector contains all classes

    # Prefer the path where the classes appear in the same order as in
    # search_cls_list.
    primary_cls = search_cls_list[0]
    matching = sort_vectors_by_primary_cls(matching, primary_cls)
    for vector in matching:
        # Remove extra classes that are not explicitly requested.
        clean_vector = [c for c in vector if c in search_cls_list]
        if clean_vector == search_cls_list:
            return vector

    return matching[0] # No vector contains all classes in the same order.

def _class2through_columns(from_cls, through_model):
    table_name = from_cls._meta.db_table
    through_table = through_model._meta.db_table
    through_left = get_field_to(through_model, from_cls).column
    through_right = table_name+'.'+from_cls._meta.pk.column
    return through_table, through_left, through_right

def _through2class_columns(through_model, target_cls):
    # From through-table to target class.
    through_table = through_model._meta.db_table
    from_field = get_field_to(through_model, target_cls)
    through_join = from_field.get_reverse_joining_columns()
    left, right = through_join[0]
    right = through_table+'.'+right
    return left, right

def _get_through_model(cls, field):
    if isinstance(field, models.fields.related.ManyToManyField):
        return getattr(cls, field.attname).through
    return None

def _get_join_data(last_cls, to_cls):
    result = []
    last_table_name = last_cls._meta.db_table

    # Two options: The current class has a reference to the other table,
    # or the other way around.
    field = get_field_to(last_cls, to_cls)
    if field:
        through_model = _get_through_model(last_cls, field)
        if through_model:
            result.append(_class2through_columns(last_cls, through_model))
            left, right = _through2class_columns(through_model, to_cls)
        else:
            left, right = field.get_reverse_joining_columns()[0]
            right = last_table_name+'.'+right

    else:
        field = get_field_to(to_cls, last_cls)
        if field is None:
            raise AttributeError('JOIN for unconnected objects is not possible')

        through_model = _get_through_model(to_cls, field)
        if through_model:
            result.append(_class2through_columns(last_cls, through_model))
            left, right = _through2class_columns(through_model, to_cls)
        else:
            left, right = field.get_joining_columns()[0]
            right = last_table_name+'.'+right

    table_name = to_cls._meta.db_table
    result.append((table_name, left, right))
    return result

def get_join_for(vector):
    """
    Given a vector as returned by get_object_vector_for(), this function
    returns a list of tuples that explain how to join the models (tables)
    together on the SQL layer. Each tuple has three elements::

        (table_name, left_key, right_key)

    In the first tuple of the list, left_key is always None.
    In the second tuple of the list, right_key is always None.
    All other tuples required both keys to join them.

    Complete example (keep in mind that the connection between Component
    and Unit is many-to-many, so there's a helper table here)::

        get_join_path_for((Device, Component, Unit))

    This returns::

        [
            ('inventory_device', None, None),
            ('inventory_component', 'device_id', 'inventory_device.metadata_id'),
            ('inventory_unit_component', 'component_id', 'inventory_component.id'),
            ('inventory_unit', 'id', 'inventory_unit_component.unit_id')
        ]

    Which means that the following SQL JOIN could be used::

        SELECT *
        FROM inventory_device
        LEFT JOIN inventory_component ON inventory_component.device_id=inventory_device.metadata_id
        LEFT JOIN inventory_unit_component ON inventory_unit_component.component_id=inventory_component.id
        LEFT JOIN inventory_unit ON inventory_unit.id=inventory_unit_component.unit_id
    """
    result = [(vector[0]._meta.db_table, None, None)]
    for pos, thecls in enumerate(vector[1:]):
        last_cls = vector[pos]
        result += _get_join_data(last_cls, thecls)
    return result
