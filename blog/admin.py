# blog/admin.py
from django.contrib import admin
from .models import Article, Comment

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('get_author', 'article', 'created_at')  # Remplacez 'user' par 'get_author'
    list_filter = ('created_at',)
    search_fields = ('content',)

    def get_author(self, obj):
        return obj.author.username
    get_author.short_description = 'Auteur'