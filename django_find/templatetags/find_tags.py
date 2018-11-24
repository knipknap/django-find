from __future__ import absolute_import, print_function
from django import template
from django.template.loader import render_to_string

class SearchNode(template.Node):
    def __init__(self, queryset_var, fields):
        self.queryset_var = template.Variable(queryset_var)
        self.fields = fields

    def render(self, context):
        request = context['request']
        getvars = request.GET.copy()

        if 'q' in getvars:
            # Search, and store the resulting queryset in the current
            # context.
            query = getvars['q']
            queryset = self.queryset_var.resolve(context)
            q_obj = queryset.model.q_from_query(query, self.fields)
            context[self.queryset_var.var] = queryset.filter(q_obj)

        return render_to_string('django_find/form.html',
                                {'getvars': getvars})

def find(parser, token):
    contents = token.split_contents()
    if len(contents) < 2:
        raise template.TemplateSyntaxError(
            "%r tag requires at least 1 argument, " +
            "in the form of {%% %r model.objects.all [alias1 alias2 ...] %%}" % contents[0])

    return SearchNode(contents[1], contents[2:])

register = template.Library()
register.tag('find', find)
