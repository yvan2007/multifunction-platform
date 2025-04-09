# blog/serializers.py
from rest_framework import serializers
from .models import Article
from ecommerce.models import Category

class ArticleSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(category_type='blog'))
    author = serializers.StringRelatedField()

    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'content', 'author', 'category', 'image']

class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']