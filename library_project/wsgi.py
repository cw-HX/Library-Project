"""WSGI config for running the Django application.

This module exposes the WSGI callable `application` which is used by WSGI
servers to forward requests to Django. It sets the default settings module
environment variable and creates the WSGI application object.
"""

import os
from django.core.wsgi import get_wsgi_application

# Ensure the DJANGO_SETTINGS_MODULE environment variable points to the
# project's settings module before creating the WSGI application.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')

# The WSGI application callable used by WSGI servers.
application = get_wsgi_application()
