from django.urls import path
from . import views
from multifunction_platform.views import add_product, product_list, product_detail, add_to_cart, cart_detail

app_name = 'ecommerce'

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    path('add-product/', add_product, name='add_product'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_detail, name='cart_detail'),
    path('toggle-favorite/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('', views.ecommerce, name='ecommerce'),
]