# ecommerce/forms.py
from django import forms
from .models import Product, ProductImage, Review  # Ajoutez Review ici

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'ckeditor5'}),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(),  # Le champ sera géré via JavaScript
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Votre commentaire...'}),
        }