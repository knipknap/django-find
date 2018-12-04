The django-find Query Language
==============================

Introduction
------------

In this chapter, we explain the query language that can be passed to
``Searchable.by_query()``.

For example:

- ``hello world`` (searches all fields for hello and world)
- ``robert OR title:road`` (searches all fields for "robert", and "title" for "road")

The basics
----------

To search all available fields, simply enter a word. For example,
the following query searches all fields for "test"::

	test

When using multiple words, the query returns all entries that match
all of the words. In other words, the following query returns all
entries that have both, 'foo' in any field AND 'bar' in any field::

	foo bar

To search for strings including whitespace, use double quotes. The
following string returns all models that have a field containing
"foo bar" (without quotes)::

	"foo bar"

Search individual fields
------------------------

To limit your search to a specific field, you can
use the following syntax::

	author:robert
	author:"robert frost"
	author:robert author:frost title:road

Limiting a search to the beginning or end of a string
-----------------------------------------------------

To search a string in a particular location of a field, use the
``^`` and ``$`` operators. To search at the beginning, use::

	^test
	author:^robert

To search a string at the end of a field, use::

	test$
	author:frost$

To look for an exact match, use either both, ``^`` and ``$``, or
use an equal sign (``=``) instead. The following queries all look
for an exact match::

	^test$
	author:^frost$
	author=frost
	author:"^robert frost$"
	author="robert frost"

Boolean operators
-----------------

Boolean AND
~~~~~~~~~~~

When you specify multiple words, django-find by default returns
all entries that match all of the words. In other words, django-find
behaves like a boolean AND. The following queries are all equivalent::

	foo bar
	foo AND bar
	foo and bar
	"foo" and "bar"

Boolean OR
~~~~~~~~~~

You can also use boolean OR operators. Here are some examples::

	"robert frost" OR "mark twain"
	robert or mark
	^robert or twain$ or foo or title:test
	author:^robert or author:twain$

Boolean NOT
~~~~~~~~~~~

To find fields that DON'T match a particular string, use NOT::

	"robert frost" not title:"the road"
	"robert frost" and not title:"the road"
	not foo or not bar

Grouping
--------

For more complex searches, you can use brackets to group sub-expressions.
Arbitrary nesting is supported::

	author:robert and not (title:"the road" or title:"yellow")
	test (name:foo and (book:one or book:two) and (chapter:10 or chapter:12 or chapter:13))

Searching dates and times
-------------------------

Date formats
~~~~~~~~~~~~

django-find accepts all formats that are supported by the
`dateparser <https://github.com/scrapinghub/dateparser>`_ python module.
Some examples::

	12/12/12
	2018-01-22
	"2018-01-22 10:00"
	"10:40 pm"
	"August 14, 2015 EST"
	"1 min ago"
	"2 weeks ago"
	"3 months, 1 week and 1 day ago"
	"in 2 days"
	tomorrow

For a full list of supported formats, please check the
`dateparser documentation <https://github.com/scrapinghub/dateparser>`_.

Searching for ranges
~~~~~~~~~~~~~~~~~~~~

You can use them to look for time ranges. The following query
returns all entries that were updated after the beginning of
January 1st, 12:00am::

	updated>=2018-1-1

Similarly, you can get the entries that were updated before 2018::

	updated<2018-1-1

To look for a range, use AND::

	updated>=2018-1-1 updated<=2019-1-1
	updated>=2018-1-1 AND updated<=2019-1-1

When searching for dates and times, the ``^`` and ``$`` characters
have special meanings: They are equivalent to ``<=`` and ``>=``. In
other words, the following queries are equivalent when used on a
DateField or DateTimeField::

	updated:^2018-1-1
	updated>=2018-1-1

To look for an exact match, use both::

	updated:"^2018-1-1 11:00$"

Operator list
-------------

Here is the full list of operators supported by **django-find**::

	name=foo -> Name matching "foo" exactly
	name:^foo$ -> Equivalent to the previous query
	name!=foo -> Name not matching "foo" exactly
	name<>foo -> Equivalent to the previous query

	name:foo -> Name containing the substring "foo"
	name!:foo -> Name not containing the substring "foo"
	name:^foo -> Name starting with the substring "foo"
	name!:^foo -> Name not starting the substring "foo"
	name:foo$ -> Name ending with the substring "foo"
	name!:foo$ -> Name not ending the substring "foo"

	id>1 -> Greater than
	id>=1 -> Greater than or equal
	id=>1 -> Greater than or equal
	id<5 -> Less than
	id<=5 -> Less than or equal
	id=>5 -> Less than or equal
	id<>5 -> Unequal
