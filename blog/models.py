# blog/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from ecommerce.models import Category  # Importer Category depuis ecommerce

class Article(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = CKEditor5Field()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        limit_choices_to={'category_type': 'blog'}  # Restreindre aux catégories de type 'blog'
    )
    tags = models.ManyToManyField('ecommerce.Tag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')  # Changé à 'published'
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_articles',
        blank=True
    )
    image = models.ImageField(upload_to='article_covers/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Comment(models.Model):
    article = models.ForeignKey(Article, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire de {self.user.username} sur {self.article.title}"