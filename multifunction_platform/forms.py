### multifunction_platform/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from users.models import CustomUser
from ecommerce.models import Product, ProductImage, Testimonial, Review
from blog.models import Article, Comment

class CustomAuthenticationForm(forms.Form):
    login_field = forms.CharField(label="Nom d'utilisateur ou Email", max_length=254)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    secret_code = forms.CharField(label="Code secret (pour les gestionnaires)", max_length=10, required=False)

class CustomUserCreationForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=150)
    email = forms.EmailField(label="Email", required=True)
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

class ManagerCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']



class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 'slug', 'tags']

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'role', 'content', 'image']

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'category', 'status']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']