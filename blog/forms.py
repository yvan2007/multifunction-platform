from django import forms
from .models import Article, Comment

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'category', 'tags', 'image']  # Adjust fields based on your Article model

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']  # Adjust fields based on your Comment model