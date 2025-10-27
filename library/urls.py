"""URLs for the `library` application.

Each path is associated with a view function defined in `library.views`.
Named URL patterns make reversing in templates/views easy.
"""

from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('books/<str:pk>/', views.book_detail, name='book_detail'),
    path('borrow/<str:pk>/', views.borrow_book, name='borrow_book'),
    path('return/<str:pk>/', views.return_book, name='return_book'),
    path('my-borrows/', views.my_borrows, name='my_borrows'),
    # admin book management
    path('admin/books/', views.admin_book_list, name='admin_book_list'),
    path('admin/books/add/', views.admin_add_book, name='admin_add_book'),
    path('admin/books/<str:pk>/edit/', views.admin_edit_book, name='admin_edit_book'),
    path('admin/books/<str:pk>/delete/', views.admin_delete_book, name='admin_delete_book'),
]
