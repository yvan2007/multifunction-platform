from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from ecommerce.models import Category, Tag  # Explicitly import Tag for clarity

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
    tags = models.ManyToManyField(Tag, blank=True)  # Use the imported Tag model
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_articles',
        blank=True
    )
    image = models.ImageField(upload_to='article_covers/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Handle duplicate slugs by appending a number (e.g., my-article, my-article-1)
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def total_likes(self):
        # Property to get the total number of likes for the article
        return self.likes.count()

    def __str__(self):
        return self.title

class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use settings.AUTH_USER_MODEL instead of User
        on_delete=models.CASCADE,
        related_name='blog_comments'  # Avoid potential clashes with other apps
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Added to track comment updates
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    @property
    def has_replies(self):
        # Property to check if the comment has replies
        return self.replies.exists()

    def __str__(self):
        return f"Commentaire de {self.author.username} sur {self.article.title}"