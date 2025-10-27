"""Root URL configuration for the project.

This module wires the project's URL patterns. We include the `library`
app URLs first so that application-level routes like `/admin/books/`
are matched by the app before the built-in Django admin site at `/admin/`.
"""

from django.contrib import admin
from django.urls import path, include


# Application URL patterns. The order matters: more specific or app-level
# routes are placed before the Django admin site if they might overlap.
urlpatterns = [
    path('', include('library.urls')),
    path('admin/', admin.site.urls),
]
