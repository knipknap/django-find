from __future__ import absolute_import, print_function
from django import template
from django.template.loader import render_to_string
from ..search import raw_search

class SearchNode(template.Node):
    def __init__(self, model_var, fields):
        self.model_var = template.Variable(model_var)
        self.fields = fields

    def render(self, context):
        request = context['request']
        getvars = request.GET.copy()

        if 'q' in getvars:
            # Search, and store the resulting queryset in the current
            # context.
            query = getvars['q']
            model_name = self.model_var.var
            model = self.model_var.resolve(context)
            queryset = model.by_query(query, self.fields)
            context['result_set'] = queryset

        return render_to_string('django_find/form.html',
                                {'getvars': getvars})

def do_search(parser, token):
    contents = token.split_contents()
    if len(contents) < 2:
        raise template.TemplateSyntaxError(
            "%r tag requires at least 1 argument, " +
            "in the form of {%% %r model [alias1 alias2 ...] %%}" % contents[0])

    return SearchNode(contents[1], contents[2:])

register = template.Library()
register.tag('search', do_search)
