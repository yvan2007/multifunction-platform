# ecommerce/urls.py
from django.urls import path
from . import views

app_name = 'ecommerce'

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('', views.ecommerce, name='ecommerce'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('add-product/', views.add_product, name='add_product'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('toggle-favorite/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('promotions/', views.promotions, name='promotions'),
]