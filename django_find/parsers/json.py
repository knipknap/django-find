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

    def parse_operators(self, termgroup, term, fieldname):
        for operator, value in term:
            if operator.startswith('not'):
                term = Not(Term(fieldname, operator[3:], value))
            else:
                term = Term(fieldname, operator, value)
            termgroup.add(term)

    def parse_terms(self, fieldgroup, terms, fieldname):
        for term in terms:
            termgroup = And()
            fieldgroup.add(termgroup)
            if not term:
                termgroup.add(Term(fieldname, 'any', ''))
                continue
            self.parse_operators(termgroup, term, fieldname)

    def parse_criteria(self, clsgroup, criteria, clsname):
        for fieldname, terms in criteria.items():
            fieldname = clsname + '.' + fieldname
            fieldgroup = Or()
            clsgroup.add(fieldgroup)
            self.parse_terms(fieldgroup, terms, fieldname)

    def parse(self, json_string):
        json_tree = json.loads(json_string, object_pairs_hook=OrderedDict)
        result = Group(is_root=True)

        for clsname, criteria in json_tree.items():
            clsgroup = And()
            result.add(clsgroup)
            self.parse_criteria(clsgroup, criteria, clsname)

        return result.optimize()
