#!/usr/bin/env python
import os
import sys


def main():
    """
    Entry point for Django's command-line utility.

    This function sets the default settings module for Django and
    delegates execution to Django's `execute_from_command_line`, which
    handles commands like `runserver`, `migrate`, and `createsuperuser`.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
    try:
        # Import the Django command executor lazily so manage.py can be
        # imported without Django being fully installed in some contexts.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and"
            " available on your PYTHONPATH environment variable? Did you"
            " forget to activate a virtual environment?"
        ) from exc
    # Pass the command-line arguments to Django's command dispatcher.
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
