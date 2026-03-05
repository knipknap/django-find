#!/usr/bin/env python
"""Thin wrapper to run tests via Django's test runner.

Prefer running tests via pytest:
    DJANGO_SETTINGS_MODULE=tests.settings pytest tests/
"""
import os
import sys

import django
from django.core.management import execute_from_command_line

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

args = [sys.argv[0], "test"]

# Allow specifying a test label from the command line.
offset = 1
try:
    sys.argv[1]
except IndexError:
    args.append(".")
else:
    if not sys.argv[1].startswith("-"):
        args.append(sys.argv[1])
        offset = 2
    else:
        args.append(".")

args.append("--verbosity=2")
args.extend(sys.argv[offset:])

execute_from_command_line(args)
