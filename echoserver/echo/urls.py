from django.urls import path
from .views import book_list, add_book, edit_book, delete_book, register, user_login, user_logout

urlpatterns = [
    path('', book_list, name='book_list'),
    path('add/', add_book, name='add_book'),
    path('edit/<int:book_id>/', edit_book, name='edit_book'),
    path('delete/<int:book_id>/', delete_book, name='delete_book'),
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
]