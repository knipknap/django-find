from __future__ import absolute_import
from django.test import TestCase
from django.test.client import RequestFactory
from django.template import Template, Context
from .models import Author

form_tmpl = '''
{% load find_tags %}
{% find object_list %}
{% for obj in object_list %}{{ obj.name }},{% endfor %}
'''.strip()

expected_form1 = '''
<form class="django-find-form" action="" method="GET">

    <input type="text" class="search-text" name="q" value=""></input>
    <input type="submit" class="search-button" value="Find"></input>
</form>

'''.lstrip()

expected_form2 = '''
<form class="django-find-form" action="" method="GET">

    <input type="hidden" name="test" value="test-value"></input>

    <input type="text" class="search-text" name="q" value=""></input>
    <input type="submit" class="search-button" value="Find"></input>
</form>

'''.lstrip()

expected_form3 = '''
<form class="django-find-form" action="" method="GET">

    <input type="hidden" name="test" value="test-value"></input>

    <input type="text" class="search-text" name="q" value="A1"></input>
    <input type="submit" class="search-button" value="Find"></input>
</form>

'''.lstrip()

expected_headers1 = '''

'''.lstrip()

class TemplateTagFindTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.factory = RequestFactory()
        self.template = Template(form_tmpl)
        self.context = Context()
        self.context['object_list'] = Author.objects.all
        for i in range(11):
            Author.objects.create(name='A'+str(i), rating=10)

    def testFind1(self):
        self.context['request'] = self.factory.get('/')
        result = self.template.render(self.context).strip()
        expected = expected_form1+'A0,A1,A2,A3,A4,A5,A6,A7,A8,A9,A10,'
        self.assertEqual(result, expected, result)

    def testFind2(self):
        self.context['request'] = self.factory.get('/?test=test-value')
        result = self.template.render(self.context).strip()
        expected = expected_form2+'A0,A1,A2,A3,A4,A5,A6,A7,A8,A9,A10,'
        self.assertEqual(result, expected, result)

    def testFind3(self):
        self.context['request'] = self.factory.get('/?test=test-value&q=A1')
        result = self.template.render(self.context).strip()
        expected = expected_form3+'A1,A10,'
        self.assertEqual(result, expected, result)
