from __future__ import absolute_import, print_function
import json
from collections import OrderedDict
from ..dom import Group, And, Or, Not, Term

class JSONParser(object):
    """
    Transforms a JSON string into a DOM. The DOM is identical to what
    QueryParser generates. Example JSON input::

        {
            "Device":
            {
                "Hostname":
                    [
                        [["contains": "s-"],["contains": "-ea1"]],
                        [["startswith", ""]]
                    ],
                "Tags":
                    [
                        [["neq":"asdasd"]]
                    ]
            }
            "Component":
            {
                "Slot": [[]]
            }
        }
    """
    def parse(self, json_string):
        json_tree = json.loads(json_string, object_pairs_hook=OrderedDict)
        result = Group(is_root=True)

        for clsname, criteria in json_tree.items():
            clsgroup = And()
            result.add(clsgroup)
            for fieldname, terms in criteria.items():
                fieldname = clsname + '.' + fieldname
                fieldgroup = Or()
                clsgroup.add(fieldgroup)
                for term in terms:
                    termgroup = And()
                    fieldgroup.add(termgroup)
                    if not term:
                        termgroup.add(Term(fieldname, 'any', ''))
                        continue
                    for operator, value in term:
                        if operator.startswith('not'):
                            term = Not(Term(fieldname, operator[3:], value))
                        else:
                            term = Term(fieldname, operator, value)
                        termgroup.add(term)

        return result.optimize()
