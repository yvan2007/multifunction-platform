from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.blog, name='blog'),
    path('add-article/', views.add_article, name='add_article'),
    path('edit-article/<int:article_id>/', views.edit_article, name='edit_article'),
    path('delete-article/<int:article_id>/', views.delete_article, name='delete_article'),
    path('like-article/<int:article_id>/', views.like_article, name='like_article'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('category/<int:category_id>/', views.articles_by_category, name='articles_by_category'),
    path('add-comment/<int:article_id>/', views.add_comment, name='add_comment'),
]