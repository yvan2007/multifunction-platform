### multifunction_platform/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from multifunction_platform.forms import CustomAuthenticationForm
from users.models import CustomUser
from ecommerce.models import Product, Cart, CartItem, Order, OrderItem, Payment, Review, Testimonial, ProductImage, Category, NewsletterSubscription, Tag
from blog.models import Article, BlogCategory, Comment
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.http import HttpResponseForbidden

# Fonction utilitaire pour vérifier si l'utilisateur est un gestionnaire
def is_manager(user):
    return user.is_authenticated and user.is_manager

# Vues pour l'authentification
def login_view(request):
    from .forms import CustomAuthenticationForm
    if request.user.is_authenticated:
        if request.user.is_manager:
            return redirect('manager_dashboard')
        return redirect('index')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login_field = form.cleaned_data.get('login_field')
            password = form.cleaned_data.get('password')

            user = None
            try:
                if '@' in login_field:
                    user = CustomUser.objects.get(email=login_field)
                else:
                    user = CustomUser.objects.get(username=login_field)
            except CustomUser.DoesNotExist:
                messages.error(request, "Utilisateur non trouvé.")
                return render(request, 'login.html', {'form': form})

            # Vérifier que l'utilisateur n'est PAS un gestionnaire
            if user.is_manager:
                messages.error(request, "Les gestionnaires doivent utiliser la page de connexion dédiée.")
                return render(request, 'login.html', {'form': form})

            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Connexion réussie !")
                return redirect('index')
            else:
                messages.error(request, "Mot de passe incorrect.")
    else:
        form = CustomAuthenticationForm()

    return render(request, 'login.html', {'form': form})

def manager_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_manager:
            return redirect('manager_dashboard')
        else:
            messages.error(request, "Vous n'êtes pas autorisé à accéder à cette page.")
            return redirect('index')

    # Vérifier si un code 2FA a été envoyé
    if '2fa_code' in request.session:
        if request.method == 'POST':
            entered_code = request.POST.get('2fa_code')
            if entered_code == request.session['2fa_code']:
                user = CustomUser.objects.get(id=request.session['user_id'])
                login(request, user)
                messages.success(request, "Connexion réussie !")
                # Nettoyer la session
                del request.session['2fa_code']
                del request.session['user_id']
                return redirect('manager_dashboard')
            else:
                messages.error(request, "Code 2FA incorrect.")
                return render(request, 'manager_login_2fa.html')
        return render(request, 'manager_login_2fa.html')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login_field = form.cleaned_data.get('login_field')
            password = form.cleaned_data.get('password')
            secret_code = form.cleaned_data.get('secret_code')

            user = None
            try:
                if '@' in login_field:
                    user = CustomUser.objects.get(email=login_field)
                else:
                    user = CustomUser.objects.get(username=login_field)
            except CustomUser.DoesNotExist:
                messages.error(request, "Utilisateur non trouvé.")
                return render(request, 'manager_login.html', {'form': form})

            if not user.is_manager:
                messages.error(request, "Vous n'êtes pas un gestionnaire. Veuillez utiliser la page de connexion client.")
                return render(request, 'manager_login.html', {'form': form})

            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                if not secret_code:
                    messages.error(request, "Le code secret est requis pour les gestionnaires.")
                    return render(request, 'manager_login.html', {'form': form})
                if secret_code != user.secret_code:
                    messages.error(request, "Code secret incorrect.")
                    return render(request, 'manager_login.html', {'form': form})

                # Générer un code 2FA
                code = ''.join(random.choices(string.digits, k=6))
                request.session['2fa_code'] = code
                request.session['user_id'] = user.id

                # Envoyer le code par email
                send_mail(
                    subject='Code de vérification 2FA',
                    message=f"Votre code de vérification est : {code}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.info(request, "Un code de vérification a été envoyé à votre email.")
                return render(request, 'manager_login_2fa.html')
            else:
                messages.error(request, "Mot de passe incorrect.")
    else:
        form = CustomAuthenticationForm()

    return render(request, 'manager_login.html', {'form': form})

def register(request):
    from .forms import CustomUserCreationForm, ManagerCreationForm
    if request.user.is_authenticated:
        return redirect('index')

    user_type = request.GET.get('user_type', 'client')
    if user_type == 'manager':
        if request.method == 'POST':
            form = ManagerCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_manager = True
                user.generate_secret_code()  # Utilise la méthode du modèle pour générer le secret_code
                user.save()
                subject = 'Votre code secret pour la connexion gestionnaire'
                message = f"Votre code secret est : {user.secret_code}"
                send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
                messages.success(request, "Inscription réussie ! Vérifiez votre email pour le code secret.")
                return redirect('users:login')
        else:
            form = ManagerCreationForm()
    else:
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, "Inscription réussie ! Vous êtes maintenant connecté.")
                return redirect('index')
        else:
            form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form, 'user_type': user_type})

def logout_view(request):
    logout(request)
    messages.success(request, "Déconnexion réussie !")
    return redirect('users:login')  # Redirige vers la page de connexion

def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            # Générer un token et un UID pour la réinitialisation
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # Construire le lien de réinitialisation
            reset_link = request.build_absolute_uri(
                reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            # Envoyer l'email
            send_mail(
                subject='Réinitialisation de votre mot de passe',
                message=f'Cliquez sur ce lien pour réinitialiser votre mot de passe : {reset_link}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "Un email de réinitialisation a été envoyé à votre adresse.")
            return redirect('users:login')
        except CustomUser.DoesNotExist:
            messages.error(request, "Aucun utilisateur avec cet email n'a été trouvé.")
    return render(request, 'password_reset.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('password')
            user.set_password(new_password)
            user.save()
            messages.success(request, "Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.")
            return redirect('users:login')
        return render(request, 'password_reset_confirm.html', {'uidb64': uidb64, 'token': token})
    else:
        messages.error(request, "Le lien de réinitialisation est invalide ou a expiré.")
        return redirect('users:password_reset')

# Vues principales
def index(request):
    cart_item_count = CartItem.objects.filter(cart__user=request.user).count() if request.user.is_authenticated else 0
    products = Product.objects.all()[:6]
    articles = Article.objects.filter(status='published')[:3]
    new_arrivals = Product.objects.order_by('-created_at')[:1]
    testimonials = Testimonial.objects.all()
    return render(request, 'index.html', {
        'cart_item_count': cart_item_count,
        'products': products,
        'articles': articles,
        'new_arrivals': new_arrivals,
        'testimonials': testimonials,
    })

def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'product_list.html', {'products': products, 'query': query})

def about(request):
    return render(request, 'about.html')

def privacy(request):
    return render(request, 'privacy.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Envoyer un email à l'administrateur
        send_mail(
            subject=f"Message de {name} - {subject}",
            message=f"De : {email}\n\nMessage :\n{message}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        messages.success(request, "Votre message a été envoyé avec succès !")
        return redirect('contact')

    return render(request, 'contact.html')

def testimonial(request):
    testimonials = Testimonial.objects.all()
    return render(request, 'testimonial.html', {'testimonials': testimonials})

def add_testimonial(request):
    if request.method == 'POST':
        from .forms import TestimonialForm
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.user = request.user
            testimonial.save()
            messages.success(request, "Témoignage ajouté avec succès !")
            return redirect('testimonial')
    else:
        from .forms import TestimonialForm
        form = TestimonialForm()
    return render(request, 'add_testimonial.html', {'form': form})

def delete_testimonial(request, testimonial_id):
    testimonial = get_object_or_404(Testimonial, id=testimonial_id)
    if request.user == testimonial.user or request.user.is_manager:
        testimonial.delete()
        messages.success(request, "Témoignage supprimé avec succès !")
    else:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce témoignage.")
    return redirect('testimonial')

def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not NewsletterSubscription.objects.filter(email=email).exists():
            NewsletterSubscription.objects.create(email=email)
            messages.success(request, "Abonnement réussi !")
        else:
            messages.error(request, "Vous êtes déjà abonné.")
        return redirect('index')
    return render(request, 'subscribe_form.html')

@login_required
def manager_dashboard(request):
    if not request.user.is_manager:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à accéder à cette page.")
    
    products = Product.objects.all()
    articles = Article.objects.all()
    testimonials = Testimonial.objects.all()
    
    if request.method == 'POST':
        # Gestion des produits
        if 'add_product' in request.POST:
            name = request.POST.get('name')
            price = request.POST.get('price')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            category = Category.objects.get(id=category_id)
            slug = name.lower().replace(' ', '-')
            Product.objects.create(name=name, price=price, description=description, category=category, slug=slug)
            messages.success(request, "Produit ajouté avec succès.")
        
        # Gestion des articles
        elif 'add_article' in request.POST:
            title = request.POST.get('title')
            content = request.POST.get('content')
            category_id = request.POST.get('category')
            category = BlogCategory.objects.get(id=category_id)
            slug = title.lower().replace(' ', '-')
            Article.objects.create(title=title, content=content, category=category, author=request.user, slug=slug, status='published')
            messages.success(request, "Article ajouté avec succès.")
        
        # Gestion des témoignages
        elif 'add_testimonial' in request.POST:
            name = request.POST.get('name')
            role = request.POST.get('role')
            content = request.POST.get('content')
            Testimonial.objects.create(name=name, role=role, content=content)
            messages.success(request, "Témoignage ajouté avec succès.")
        
        # Suppression
        elif 'delete_product' in request.POST:
            product_id = request.POST.get('product_id')
            Product.objects.filter(id=product_id).delete()
            messages.success(request, "Produit supprimé avec succès.")
        
        elif 'delete_article' in request.POST:
            article_id = request.POST.get('article_id')
            Article.objects.filter(id=article_id).delete()
            messages.success(request, "Article supprimé avec succès.")
        
        elif 'delete_testimonial' in request.POST:
            testimonial_id = request.POST.get('testimonial_id')
            Testimonial.objects.filter(id=testimonial_id).delete()
            messages.success(request, "Témoignage supprimé avec succès.")
        
        return redirect('manager_dashboard')

    categories = Category.objects.all()
    blog_categories = BlogCategory.objects.all()
    return render(request, 'manager_dashboard.html', {
        'products': products,
        'articles': articles,
        'testimonials': testimonials,
        'categories': categories,
        'blog_categories': blog_categories,
    })

# Vues pour la gestion des catégories
@login_required
@user_passes_test(is_manager)
def manage_categories(request):
    product_categories = Category.objects.filter(category_type='product')
    blog_categories = BlogCategory.objects.all()
    return render(request, 'manage_categories.html', {'product_categories': product_categories, 'blog_categories': blog_categories})

@login_required
@user_passes_test(is_manager)
def add_product_category(request):
    if request.method == 'POST':
        from .forms import ProductCategoryForm
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie de produit ajoutée avec succès !")
            return redirect('manage_categories')
    else:
        from .forms import ProductCategoryForm
        form = ProductCategoryForm()
    return render(request, 'add_category.html', {'form': form, 'category_type': 'product'})

@login_required
@user_passes_test(is_manager)
def add_blog_category(request):
    if request.method == 'POST':
        from .forms import BlogCategoryForm
        form = BlogCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie de blog ajoutée avec succès !")
            return redirect('manage_categories')
    else:
        from .forms import BlogCategoryForm
        form = BlogCategoryForm()
    return render(request, 'add_category.html', {'form': form, 'category_type': 'blog'})

@login_required
@user_passes_test(is_manager)
def delete_product_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, category_type='product')
    category.delete()
    messages.success(request, "Catégorie de produit supprimée avec succès !")
    return redirect('manage_categories')

@login_required
@user_passes_test(is_manager)
def delete_blog_category(request, category_id):
    category = get_object_or_404(BlogCategory, id=category_id)
    category.delete()
    messages.success(request, "Catégorie de blog supprimée avec succès !")
    return redirect('manage_categories')

# Vues pour Ecommerce
@login_required
@user_passes_test(is_manager)
def add_product(request):
    if request.method == 'POST':
        from .forms import ProductForm
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            for image in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(product=product, image=image)
            messages.success(request, "Produit ajouté avec succès !")
            return redirect('ecommerce:product_list')
    else:
        from .forms import ProductForm
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'ecommerce/product_list.html', {'products': products})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    reviews = Review.objects.filter(product=product)
    if request.method == 'POST':
        from .forms import ReviewForm
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(request, "Avis ajouté avec succès !")
            return redirect('ecommerce:product_detail', slug=slug)
    else:
        from .forms import ReviewForm
        form = ReviewForm()
    return render(request, 'ecommerce/product_detail.html', {'product': product, 'related_products': related_products, 'reviews': reviews, 'form': form})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, "Produit ajouté au panier !")
    return redirect('orders:cart')

def cart_detail(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return render(request, 'ecommerce/cart.html', {'cart': cart})
    else:
        messages.error(request, "Veuillez vous connecter pour voir votre panier.")
        return redirect('users:login')

# Vues pour Blog
def blog(request):
    articles = Article.objects.all()
    categories = BlogCategory.objects.all()
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
    article = get_object_or_404(Article, slug=slug)
    comments = article.comments.all()
    return render(request, 'blog/article_detail.html', {'article': article, 'comments': comments})

def articles_by_category(request, category_id):
    category = get_object_or_404(BlogCategory, id=category_id)
    articles = Article.objects.filter(category=category)
    categories = BlogCategory.objects.all()
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