# ecommerce/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ProductViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]