from django.urls import path
from .views import book_list, add_book, edit_book, delete_book, register, user_login, user_logout, profile, add_to_cart, \
    view_cart, remove_from_cart, order_history, order_detail, checkout, change_password

urlpatterns = [
    path('', book_list, name='book_list'),
    path('add/', add_book, name='add_book'),
    path('edit/<int:book_id>/', edit_book, name='edit_book'),
    path('delete/<int:book_id>/', delete_book, name='delete_book'),
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('add-to-cart/<int:book_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', view_cart, name='view_cart'),
    path('cart/remove/<int:cart_item_id>/', remove_from_cart, name='remove_from_cart'),
    path('checkout/', checkout, name='checkout'),
    path('orders/', order_history, name='order_history'),
    path('orders/<int:order_id>/', order_detail, name='order_detail'),
    path('profile/change-password/', change_password, name='change_password')
]