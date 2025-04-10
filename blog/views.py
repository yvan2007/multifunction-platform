from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CommentForm
from .models import Article, Comment
from ecommerce.models import Category

# Move ArticleForm to blog.forms for better organization
from .forms import ArticleForm  # Changed from users.forms to blog.forms

def blog(request):
    categories = Category.objects.filter(category_type='blog', is_active=True)
    selected_category = None
    if 'category' in request.GET:
        selected_category = get_object_or_404(Category, id=request.GET.get('category'), category_type='blog')
        articles = Article.objects.filter(category=selected_category, status='published')
    else:
        articles = Article.objects.filter(status='published')
    
    if not categories.exists():
        messages.warning(request, "Aucune catégorie de blog disponible.")
        articles = Article.objects.none()

    return render(request, 'blog/article_list.html', {
        'articles': articles,
        'categories': categories,
        'selected_category': selected_category,
    })

@login_required
def add_article(request):
    categories = Category.objects.filter(category_type='blog', is_active=True)
    if not categories.exists():
        messages.warning(request, "Aucune catégorie de blog disponible. Veuillez en créer une avant d'ajouter un article.")
        return redirect('users:manage_categories')

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.status = 'published'  # Explicitly set status
            article.save()
            form.save_m2m()
            messages.success(request, "Article ajouté avec succès !")
            return redirect('blog:blog')
        else:
            messages.error(request, "Erreur lors de l'ajout de l'article. Veuillez vérifier les champs.")
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
            messages.error(request, "Erreur lors de la modification de l'article. Veuillez vérifier les champs.")
    else:
        form = ArticleForm(instance=article)
    return render(request, 'blog/edit_article.html', {'form': form, 'article': article})

@login_required
def delete_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.user != article.author and not request.user.is_manager:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer cet article.")
        return redirect('blog:blog')
    
    if request.method == 'POST':  # Require POST to delete for safety
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
    article = get_object_or_404(Article, slug=slug, status='published')
    comments = article.comments.all()
    return render(request, 'blog/article_detail.html', {
        'article': article,
        'comments': comments,
        'is_liked': request.user in article.likes.all() if request.user.is_authenticated else False,
    })

def articles_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, category_type='blog')
    articles = Article.objects.filter(category=category, status='published')
    categories = Category.objects.filter(category_type='blog', is_active=True)
    return render(request, 'blog/article_list.html', {
        'articles': articles,
        'categories': categories,
        'selected_category': category,
    })

@login_required
def add_comment(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.save()
            messages.success(request, "Votre commentaire a été ajouté avec succès !")
            return redirect('blog:article_detail', slug=article.slug)
        else:
            messages.error(request, "Erreur lors de l'ajout du commentaire. Veuillez vérifier votre saisie.")
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment.html', {'form': form, 'article': article})