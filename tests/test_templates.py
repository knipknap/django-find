from __future__ import absolute_import
from django.test import TestCase
from django.test.client import RequestFactory
from django.template import Template, Context
from django.template.loader import render_to_string
from .models import Author, Book

expected_headers = '''
<tr>
<th>Name</th><th>The title</th><th>Comment</th><th>Stars</th><th>AuthorID</th>
</tr>
'''.strip()

class HeadersTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.context = {'object_list': Book.objects.all}
        author = Author.objects.create(name='MyAuthor', rating=2)
        for i in range(11):
            Book.objects.create(author=author, title='B'+str(i), rating=10)

    def testHeaders1(self):
        result = render_to_string('django_find/headers.html', self.context)
        self.assertEqual(result.strip(), expected_headers, result)
