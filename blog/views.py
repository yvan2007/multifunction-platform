# blog/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Article, Comment
from ecommerce.models import Category

def blog(request):
    articles = Article.objects.filter(status='published')  # Ne montrer que les articles publiés
    categories = Category.objects.filter(category_type='blog')
    return render(request, 'blog/article_list.html', {'articles': articles, 'categories': categories})

@login_required
def add_article(request):
    if request.method == 'POST':
        from .forms import ArticleForm
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            form.save_m2m()
            messages.success(request, "Article ajouté avec succès !")
            return redirect('blog:blog')
    else:
        from .forms import ArticleForm
        form = ArticleForm()
    return render(request, 'add_article.html', {'form': form})

@login_required
def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.user != article.author and not request.user.is_manager:
        messages.error(request, "Vous n'êtes pas autorisé à modifier cet article.")
        return redirect('blog:blog')
    if request.method == 'POST':
        from .forms import ArticleForm
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article modifié avec succès !")
            return redirect('blog:blog')
    else:
        from .forms import ArticleForm
        form = ArticleForm(instance=article)
    return render(request, 'edit_article.html', {'form': form, 'article': article})

@login_required
def delete_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.user != article.author and not request.user.is_manager:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer cet article.")
        return redirect('blog:blog')
    article.delete()
    messages.success(request, "Article supprimé avec succès !")
    return redirect('blog:blog')

@login_required
def like_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.user in article.likes.all():
        article.likes.remove(request.user)
        messages.success(request, "Article retiré des favoris.")
    else:
        article.likes.add(request.user)
        messages.success(request, "Article ajouté aux favoris !")
    return redirect('blog:article_detail', slug=article.slug)

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, status='published')  # Ne montrer que les articles publiés
    comments = article.comments.all()
    return render(request, 'blog/article_detail.html', {'article': article, 'comments': comments})

def articles_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, category_type='blog')
    articles = Article.objects.filter(category=category, status='published')  # Ne montrer que les articles publiés
    categories = Category.objects.filter(category_type='blog')
    return render(request, 'blog/article_list.html', {'articles': articles, 'categories': categories, 'selected_category': category})

@login_required
def add_comment(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        from .forms import CommentForm
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
            messages.success(request, "Commentaire ajouté avec succès !")
            return redirect('blog:article_detail', slug=article.slug)
    else:
        from .forms import CommentForm
        form = CommentForm()
    return render(request, 'blog/comment_form.html', {'form': form, 'article': article})