from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from ecommerce.api import ProductViewSet, CategoryViewSet
from blog.api import ArticleViewSet
from .views import (
    index, search_products, about, privacy, contact, testimonial,
    add_testimonial, delete_testimonial, subscribe, manage_categories,
    add_product_category, add_blog_category, delete_product_category,
    delete_blog_category, manager_dashboard
)

# Define app_name for the root URLs (optional but recommended)
app_name = 'core'

# Set up the DefaultRouter for API views
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')  # Added CategoryViewSet
router.register(r'articles', ArticleViewSet, basename='article')

# Swagger/Redoc schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Multifunction Platform API",
        default_version='v1',
        description="API for accessing products, categories, and articles",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="kouayavana19@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # App-specific URL includes with namespaces
    path('orders/', include('orders.urls', namespace='orders')),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('blog/', include('blog.urls', namespace='blog')),
    path('ecommerce/', include('ecommerce.urls', namespace='ecommerce')),
    path('users/', include('users.urls', namespace='users')),
    
    # Core application views
    path('', index, name='index'),
    path('search/', search_products, name='search_products'),
    path('about/', about, name='about'),
    path('privacy/', privacy, name='privacy'),
    path('contact/', contact, name='contact'),
    path('testimonial/', testimonial, name='testimonial'),
    path('add-testimonial/', add_testimonial, name='add_testimonial'),
    path('delete-testimonial/<int:testimonial_id>/', delete_testimonial, name='delete_testimonial'),
    path('subscribe/', subscribe, name='subscribe'),
    
    # Category management views
    path('manage-categories/', manage_categories, name='manage_categories'),
    path('add-product-category/', add_product_category, name='add_product_category'),
    path('add-blog-category/', add_blog_category, name='add_blog_category'),
    path('delete-product-category/<int:category_id>/', delete_product_category, name='delete_product_category'),
    path('delete-blog-category/<int:category_id>/', delete_blog_category, name='delete_blog_category'),
    
    # Manager dashboard
    path('manager-dashboard/', manager_dashboard, name='manager_dashboard'),
    
    # API and documentation endpoints
    path('api-auth/', include('rest_framework.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/', include('ecommerce.api_urls')),
    
    # CKEditor 5 file upload
    path('ckeditor5/', include('django_ckeditor_5.urls'), name='ck_editor_5_upload_file'),
]

# Serve static and media files in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)