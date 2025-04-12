from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.blog, name='blog'),
    path('add/', views.add_article, name='add_article'),
    path('edit/<int:article_id>/', views.edit_article, name='edit_article'),
    path('delete-article/<int:article_id>/', views.delete_article, name='delete_article'),
    path('like-article/<int:article_id>/', views.like_article, name='like_article'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),  # Changed from <slug:slug> to <int:article_id>
    path('category/<int:category_id>/', views.articles_by_category, name='articles_by_category'),
    path('article/<int:article_id>/comment/', views.add_comment, name='add_comment'),  # Updated to use article_id
    path('article/<int:article_id>/comment/<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),  # Updated to use article_id
    
]