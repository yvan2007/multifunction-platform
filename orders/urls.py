### orders/urls.py
from django.urls import path
from .views import cart, add_to_cart, checkout, order_history, order_detail

app_name = 'orders'

urlpatterns = [
    path('cart/', cart, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('checkout/', checkout, name='checkout'),
    path('order-history/', order_history, name='order_history'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
]