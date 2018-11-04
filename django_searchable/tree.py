from __future__ import absolute_import, print_function

class Node(object):
    def __init__(self, children=None, is_root=False):
        if isinstance(children, Node):
            children = [children]
        self.is_root = is_root
        self.children = list(children) if children else []

    def add(self, child):
        self.children.append(child)
        return child

    def pop(self):
        return self.children.pop()

    def dump(self, indent=0):
        isroot = '(root)' if self.is_root else ''
        result = [(indent * '  ') + self.__class__.__name__ + isroot]
        for child in self.children:
            result += child.dump(indent+1)
        if self.is_root:
            return '\n'.join(result)
        return result

    def each(self, func, node_type=None):
        """
        Runs func once for every node in the object tree.
        If node_type is not None, only call func for nodes with the given
        type.
        """
        if node_type is None or isinstance(self, node_type):
            func(self)
        for child in self.children:
            child.each(func, node_type)
