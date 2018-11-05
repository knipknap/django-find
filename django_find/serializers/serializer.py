
class Serializer(object):
    """
    Base class for all serializers.
    """

    def logical_root_group(self, root_group, terms):
        return self.logical_group(terms)

    def logical_group(self, terms):
        return self.logical_and(terms)
