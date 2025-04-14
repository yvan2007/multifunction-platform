from django import forms
from .models import Article, Comment
from django_ckeditor_5.widgets import CKEditor5Widget

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'slug', 'category', 'content', 'tags', 'image', 'status']  # Ajout de tags et status
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'content': CKEditor5Widget(),  # Utiliser CKEditor5Widget
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: tech, blog, actu...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Écrivez votre commentaire ici...',
            }),
        }
        labels = {
            'content': 'Votre commentaire',
        }