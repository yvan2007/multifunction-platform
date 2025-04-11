from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Article, Comment, Category
from .forms import ArticleForm, CommentForm

def blog(request):
    articles = Article.objects.all()
    categories = Category.objects.filter(category_type='blog')  # Filtrer par category_type='blog'
    return render(request, 'blog/article_list.html', {'articles': articles, 'categories': categories})

@login_required
def add_article(request):
    if not request.user.is_manager:
        return redirect('blog')  # Redirect if the user is not a manager

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            return redirect('blog')
    else:
        form = ArticleForm()
    
    return render(request, 'blog/add_article.html', {'form': form})

@login_required
def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.user != article.author and not request.user.is_manager:
        messages.error(request, "Vous n'êtes pas autorisé à modifier cet article.")
        return redirect('blog:blog')
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article modifié avec succès !")
            return redirect('blog:blog')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'blog/edit_article.html', {'form': form, 'article': article})

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
    article = get_object_or_404(Article, slug=slug)
    comments = article.comments.filter(parent=None)  # N'afficher que les commentaires de premier niveau
    form = CommentForm()
    return render(request, 'blog/article_detail.html', {'article': article, 'comments': comments, 'form': form})

def articles_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, category_type='blog')  # Filtrer par category_type='blog'
    articles = Article.objects.filter(category=category)
    categories = Category.objects.filter(category_type='blog')  # Filtrer par category_type='blog'
    return render(request, 'blog/article_list.html', {'articles': articles, 'categories': categories, 'selected_category': category})

@login_required
def add_comment(request, article_slug):
    article = get_object_or_404(Article, slug=article_slug)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
            messages.success(request, "Commentaire ajouté avec succès !")
            return redirect('blog:article_detail', slug=article.slug)
    else:
        form = CommentForm()
    return render(request, 'blog/comment_form.html', {'form': form, 'article': article})

@login_required
def reply_comment(request, article_slug, comment_id):
    article = get_object_or_404(Article, slug=article_slug)
    parent_comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.article = article
            reply.author = request.user
            reply.parent = parent_comment
            reply.save()
            messages.success(request, "Réponse ajoutée avec succès !")
            return redirect('blog:article_detail', slug=article.slug)
    else:
        form = CommentForm()
    return render(request, 'blog/comment_form.html', {'form': form, 'article': article, 'parent_comment': parent_comment})