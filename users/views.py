from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.contrib import messages as django_messages
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.views import PasswordResetView

# Import des modèles
from .models import CustomUser, Profile, Address, Favorite, Message
from ecommerce.models import Category, Product, Cart, CartItem
from orders.models import Order
from blog.models import Article

# Import des formulaires
from .forms import (
    CustomAuthenticationForm, CustomUserCreationForm, ManagerCreationForm,
    ProductForm, ProductImageForm, ProfileForm, AddressForm, ArticleForm, CategoryForm
)

import random
import string

# ------------------- Fonctions utilitaires -------------------

def is_manager(user):
    """Vérifie si l'utilisateur est un gestionnaire."""
    return user.is_authenticated and user.is_manager

def manager_required(view_func):
    """Décorateur pour restreindre l'accès aux gestionnaires uniquement."""
    return login_required(user_passes_test(is_manager)(view_func))

def validate_login_credentials(request, form, is_manager_login=False):
    """Valide les identifiants de connexion."""
    if not form.is_valid():
        django_messages.error(request, "Erreur lors de la connexion. Veuillez vérifier les champs.")
        return None, None

    login_field = form.cleaned_data.get('username')
    password = form.cleaned_data.get('password')
    print(f"Validation - login_field: {login_field}, password: {password}")

    if not login_field or not password:
        django_messages.error(request, "Le nom d'utilisateur/email et le mot de passe sont requis.")
        return None, None

    try:
        user = CustomUser.objects.get(Q(username=login_field) | Q(email=login_field))
        user = authenticate(request, username=user.username, password=password)
    except CustomUser.DoesNotExist:
        user = None

    print("Résultat authenticate:", user)
    if user is None:
        django_messages.error(request, "Nom d'utilisateur/email ou mot de passe incorrect.")
        return None, None

    if is_manager_login and not user.is_manager:
        django_messages.error(request, "Vous n’êtes pas un gestionnaire. Utilisez la page de connexion client (/users/login/).")
        return None, None
    elif not is_manager_login and user.is_manager:
        django_messages.error(request, "Les gestionnaires doivent utiliser la page de connexion dédiée (/users/manager-login/).")
        return None, None

    return user, password

def get_cart_item_count(user):
    """Calcule le nombre d'articles dans le panier de l'utilisateur."""
    if user.is_authenticated:
        return CartItem.objects.filter(cart__user=user).count()
    return 0

# ------------------- Vues pour l'authentification -------------------

def login_view(request):
    """Connexion pour les utilisateurs réguliers (clients)."""
    if request.user.is_authenticated:
        if request.user.is_manager:
            return redirect('users:manager_dashboard')
        return redirect('index')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        user, _ = validate_login_credentials(request, form, is_manager_login=False)
        if user is not None:
            login(request, user)
            if 'cart' in request.session:
                cart, created = Cart.objects.get_or_create(user=user)
                session_cart = request.session['cart']
                for product_id, quantity in session_cart.items():
                    product = get_object_or_404(Product, id=int(product_id))
                    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                    if created:
                        cart_item.quantity = quantity
                    else:
                        cart_item.quantity += quantity
                    cart_item.save()
                del request.session['cart']
                request.session.modified = True
            next_url = request.GET.get('next', 'index')
            django_messages.success(request, "Connexion réussie !")
            return redirect(next_url if not user.is_manager else 'users:manager_dashboard')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'users/login.html', {'form': form, 'cart_item_count': get_cart_item_count(request.user)})

def manager_login_view(request):
    """Connexion pour les gestionnaires avec 2FA."""
    if request.user.is_authenticated:
        if request.user.is_manager:
            return redirect('users:manager_dashboard')
        else:
            django_messages.error(request, "Vous n'êtes pas autorisé à accéder à cette page.")
            return redirect('index')

    if '2fa_code' in request.session:
        if request.method == 'POST':
            entered_code = request.POST.get('2fa_code')
            if entered_code == request.session['2fa_code']:
                user = CustomUser.objects.get(id=request.session['user_id'])
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                django_messages.success(request, "Connexion réussie !")
                del request.session['2fa_code']
                del request.session['user_id']
                return redirect('users:manager_dashboard')
            else:
                django_messages.error(request, "Code 2FA incorrect.")
                return render(request, 'users/manager_login_2fa.html', {'cart_item_count': get_cart_item_count(request.user)})
        return render(request, 'users/manager_login_2fa.html', {'cart_item_count': get_cart_item_count(request.user)})

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        user, password = validate_login_credentials(request, form, is_manager_login=True)
        if user is not None:
            secret_code = form.cleaned_data.get('secret_code')
            if not secret_code:
                django_messages.error(request, "Le code secret est requis pour les gestionnaires.")
                return render(request, 'users/manager_login.html', {'form': form, 'cart_item_count': get_cart_item_count(request.user)})
            if secret_code != user.secret_code:
                django_messages.error(request, "Code secret incorrect.")
                return render(request, 'users/manager_login.html', {'form': form, 'cart_item_count': get_cart_item_count(request.user)})

            code = ''.join(random.choices(string.digits, k=6))
            request.session['2fa_code'] = code
            request.session['user_id'] = user.id

            try:
                send_mail(
                    subject='Code de vérification 2FA',
                    message=f"Votre code de vérification est : {code}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                django_messages.info(request, "Un code de vérification a été envoyé à votre email.")
            except Exception as e:
                django_messages.error(request, "Erreur lors de l'envoi du code 2FA. Veuillez réessayer plus tard.")
                return render(request, 'users/manager_login.html', {'form': form, 'cart_item_count': get_cart_item_count(request.user)})
            return render(request, 'users/manager_login_2fa.html', {'cart_item_count': get_cart_item_count(request.user)})
    else:
        form = CustomAuthenticationForm()

    return render(request, 'users/manager_login.html', {'form': form, 'cart_item_count': get_cart_item_count(request.user)})

def register(request):
    """Inscription pour les utilisateurs (clients ou gestionnaires)."""
    user_type = request.GET.get('user_type', 'client')
    
    if user_type == 'manager':
        if request.method == 'POST':
            form = ManagerCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_manager = True
                user.generate_secret_code()  # Méthode définie dans CustomUser
                user.save()
                try:
                    send_mail(
                        subject='Votre code secret pour la connexion gestionnaire',
                        message=f"Votre code secret est : {user.secret_code}",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    django_messages.success(request, "Inscription réussie ! Vérifiez votre email pour le code secret.")
                except Exception as e:
                    django_messages.error(request, "Inscription réussie, mais erreur lors de l'envoi du code secret. Contactez l'administrateur.")
                return redirect('users:login')
        else:
            form = ManagerCreationForm()
    else:
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                if CustomUser.objects.filter(username=username).exists():
                    django_messages.error(request, "Ce nom d'utilisateur est déjà pris.")
                    return render(request, 'users/register.html', {'form': form, 'user_type': user_type, 'cart_item_count': get_cart_item_count(request.user)})
                user = form.save()
                Profile.objects.create(user=user)
                password = form.cleaned_data.get('password1')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    django_messages.success(request, "Inscription réussie ! Vous êtes maintenant connecté.")
                    return redirect('index')
                else:
                    django_messages.error(request, "Erreur lors de la connexion automatique. Veuillez vous connecter manuellement.")
                    return redirect('users:login')
        else:
            form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form, 'user_type': user_type, 'cart_item_count': get_cart_item_count(request.user)})

class CustomPasswordResetView(PasswordResetView):
    """Vue personnalisée pour la réinitialisation du mot de passe."""
    template_name = 'users/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')

    def custom_capitalize(self, value, style='upper'):
        if not isinstance(value, str):
            return value
        if style == 'upper':
            return value.upper()
        elif style == 'lower':
            return value.lower()
        elif style == 'title':
            return value.title()
        elif style == 'first':
            return value.capitalize()
        return value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title_text = self.custom_capitalize("Réinitialisation du mot de passe", "title")
        heading_text = self.custom_capitalize("Réinitialisation du mot de passe", "upper")
        description_text = self.custom_capitalize(
            "Entrez votre adresse e-mail ci-dessous, et nous vous enverrons un lien pour réinitialiser votre mot de passe.",
            "lower"
        )
        context['title_text'] = title_text
        context['heading_text'] = heading_text
        context['description_text'] = description_text
        context['cart_item_count'] = get_cart_item_count(self.request.user)  # Added
        return context

    def form_valid(self, form):
        current_site = get_current_site(self.request)
        site_name = current_site.name
        email_context = form.get_context()
        email_context['site_name_upper'] = site_name.upper()
        email_context['site_name_lower'] = site_name.lower()
        email_context['site_name_title'] = site_name.title()
        opts = {
            'use_https': self.request.is_secure(),
            'from_email': settings.EMAIL_HOST_USER,
            'request': self.request,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'extra_email_context': email_context,
        }
        form.save(**opts)
        return super().form_valid(form)

# ------------------- Vues pour les utilisateurs -------------------

@login_required
def profile(request):
    """Afficher le profil de l'utilisateur."""
    return render(request, 'users/profile.html', {'user': request.user, 'cart_item_count': get_cart_item_count(request.user)})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'users/edit_profile.html', {'form': form, 'cart_item_count': get_cart_item_count(request.user)})

@login_required
def account_settings(request):
    """Gérer les paramètres du compte (profil et adresses)."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    addresses = request.user.addresses.all()

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=profile)
        address_form = AddressForm(request.POST)
        if profile_form.is_valid():
            profile_form.save()
            django_messages.success(request, "Profil mis à jour avec succès !")
        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = request.user
            address.save()
            django_messages.success(request, "Adresse ajoutée avec succès !")
        return redirect('users:account_settings')
    else:
        profile_form = ProfileForm(instance=profile)
        address_form = AddressForm()

    return render(request, 'users/account_settings.html', {
        'profile_form': profile_form,
        'address_form': address_form,
        'addresses': addresses,
        'cart_item_count': get_cart_item_count(request.user),
    })

@login_required
def favorites(request):
    """Gérer les favoris de l'utilisateur."""
    favorites = request.user.favorites.all()
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        product = get_object_or_404(Product, id=product_id)
        if action == 'add':
            Favorite.objects.get_or_create(user=request.user, product=product)
            django_messages.success(request, f"{product.name} ajouté aux favoris !")
        elif action == 'remove':
            Favorite.objects.filter(user=request.user, product=product).delete()
            django_messages.success(request, f"{product.name} retiré des favoris !")
        return redirect('users:favorites')
    return render(request, 'users/favorites.html', {'favorites': favorites, 'cart_item_count': get_cart_item_count(request.user)})

@login_required
def user_messages(request):
    """Afficher les messages envoyés et reçus par l'utilisateur."""
    sent_messages = request.user.sent_messages.all()
    received_messages = request.user.received_messages.all()
    return render(request, 'users/messages.html', {
        'sent_messages': sent_messages,
        'received_messages': received_messages,
        'cart_item_count': get_cart_item_count(request.user),
    })

@login_required
def orders(request):
    """Afficher les commandes de l'utilisateur."""
    orders = Order.objects.filter(user=request.user)
    return render(request, 'users/orders.html', {'orders': orders, 'cart_item_count': get_cart_item_count(request.user)})

# ------------------- Vues pour les gestionnaires -------------------

@manager_required
def manager_dashboard(request):
    """Tableau de bord des gestionnaires."""
    filter_type = request.GET.get('filter', 'newest')

    article_count = Article.objects.filter(status='published').count()
    category_count = Category.objects.filter(category_type='product', is_active=True).count()
    product_count = Product.objects.filter(is_active=True).count()
    order_count = Order.objects.count()

    if filter_type == 'alpha':
        recent_articles = Article.objects.filter(status='published').order_by('title')[:5]
        recent_products = Product.objects.filter(is_active=True).order_by('name')[:5]
        recent_orders = Order.objects.select_related('user').order_by('user__username')[:5]
        recent_categories = Category.objects.filter(category_type='product', is_active=True).order_by('name')[:5]
    else:
        recent_articles = Article.objects.filter(status='published').order_by('-created_at')[:5]
        recent_products = Product.objects.filter(is_active=True).order_by('-created_at')[:5]
        recent_orders = Order.objects.all().order_by('-created_at')[:5]
        recent_categories = Category.objects.filter(category_type='product', is_active=True).order_by('-created_at')[:5]

    context = {
        'article_count': article_count,
        'category_count': category_count,
        'product_count': product_count,
        'order_count': order_count,
        'recent_articles': recent_articles,
        'recent_products': recent_products,
        'recent_orders': recent_orders,
        'recent_categories': recent_categories,
        'filter_type': filter_type,
        'cart_item_count': get_cart_item_count(request.user),
    }
    return render(request, 'users/manager_dashboard.html', context)

# Gestion des articles
@manager_required
def manage_articles(request):
    """Gérer les articles (CRUD)."""
    categories = Category.objects.filter(category_type='blog', is_active=True)
    if not categories.exists():
        django_messages.warning(request, "Aucune catégorie de blog disponible. Veuillez en créer une avant d'ajouter un article.")
        articles = Article.objects.none()  # Aucun article si aucune catégorie
    else:
        articles = Article.objects.all()
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            article_id = request.POST.get('article_id')
            article = get_object_or_404(Article, id=article_id)
            article.delete()
            django_messages.success(request, "Article supprimé avec succès.")
            return redirect('users:manage_articles')
        else:
            form = ArticleForm(request.POST, request.FILES)
            if form.is_valid():
                article = form.save(commit=False)
                article.author = request.user
                article.status = 'published'
                article.save()
                form.save_m2m()
                django_messages.success(request, "Article créé avec succès.")
                return redirect('users:manage_articles')
    else:
        form = ArticleForm()

    return render(request, 'users/manage_articles.html', {
        'articles': articles,
        'form': form,
        'cart_item_count': get_cart_item_count(request.user),
    })

@manager_required
def add_article(request):
    """Ajouter un nouvel article."""
    categories = Category.objects.filter(category_type='blog', is_active=True)
    if not categories.exists():
        django_messages.warning(request, "Aucune catégorie de blog disponible. Veuillez en créer une avant d'ajouter un article.")
        return redirect('users:manage_categories')

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.status = 'published'
            article.save()
            form.save_m2m()
            django_messages.success(request, "Article ajouté avec succès.")
            return redirect('users:manage_articles')
    else:
        form = ArticleForm()
    return render(request, 'users/add_article.html', {'form': form, 'cart_item_count': get_cart_item_count(request.user)})

@manager_required
def edit_article(request, article_id):
    """Modifier un article existant."""
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Article mis à jour avec succès.")
            return redirect('users:manage_articles')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'users/edit_article.html', {'form': form, 'article': article, 'cart_item_count': get_cart_item_count(request.user)})

# Gestion des catégories
@manager_required
def manage_categories(request):
    """Gérer les catégories (CRUD)."""
    filter_type = request.GET.get('filter', 'newest')
    search_query = request.GET.get('search', '')

    categories = Category.objects.filter(is_active=True)  # Afficher toutes les catégories (Blog et Produit)
    if search_query:
        categories = categories.filter(name__icontains=search_query)

    if filter_type == 'alpha':
        categories = categories.order_by('name')
    else:
        categories = categories.order_by('-created_at')

    if request.method == 'POST':
        if 'delete' in request.POST:
            category_id = request.POST.get('category_id')
            category = get_object_or_404(Category, id=category_id)
            category.delete()
            django_messages.success(request, "Catégorie supprimée avec succès.")
            return redirect('users:manage_categories')
        else:
            form = CategoryForm(request.POST)
            if form.is_valid():
                category = form.save(commit=False)
                category.is_active = True
                category.save()
                django_messages.success(request, "Catégorie créée avec succès.")
                return redirect('users:manage_categories')
    else:
        form = CategoryForm()

    return render(request, 'users/manage_categories.html', {
        'categories': categories,
        'form': form,
        'filter_type': filter_type,
        'cart_item_count': get_cart_item_count(request.user),
    })

@manager_required
def add_category(request):
    """Ajouter une nouvelle catégorie."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.is_active = True
            category.save()
            django_messages.success(request, "Catégorie ajoutée avec succès.")
            return redirect('users:manage_categories')
    else:
        form = CategoryForm()
    return render(request, 'users/add_category.html', {'form': form, 'cart_item_count': get_cart_item_count(request.user)})

@manager_required
def edit_category(request, category_id):
    """Modifier une catégorie existante."""
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Catégorie mise à jour avec succès.")
            return redirect('users:manage_categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'users/edit_category.html', {'form': form, 'category': category, 'cart_item_count': get_cart_item_count(request.user)})

# Gestion des produits
@manager_required
def manage_products(request):
    """Gérer les produits (CRUD)."""
    filter_type = request.GET.get('filter', 'newest')
    search_query = request.GET.get('search', '')

    categories = Category.objects.filter(category_type='product', is_active=True)
    if not categories.exists():
        django_messages.warning(request, "Aucune catégorie de produit disponible. Veuillez en créer une avant d'ajouter un produit.")
        products = Product.objects.none()  # Aucun produit si aucune catégorie
    else:
        products = Product.objects.filter(is_active=True)
        if search_query:
            products = products.filter(name__icontains=search_query)

        if filter_type == 'alpha':
            products = products.order_by('name')
        else:
            products = products.order_by('-created_at')

    if request.method == 'POST':
        if 'delete' in request.POST:
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            product.delete()
            django_messages.success(request, "Produit supprimé avec succès.")
            return redirect('users:manage_products')
        else:
            # Gestion du formulaire dans le modal
            form = ProductForm(request.POST)
            image_form = ProductImageForm(request.POST, request.FILES)
            if form.is_valid() and image_form.is_valid():
                product = form.save(commit=False)
                product.is_active = True
                product.save()
                form.save_m2m()
                if image_form.cleaned_data['image']:  # Vérifier si une image a été uploadée
                    image = image_form.save(commit=False)
                    image.product = product
                    image.save()
                django_messages.success(request, "Produit ajouté avec succès.")
                return redirect('users:manage_products')

    # Pour le GET, passer les formulaires au contexte
    form = ProductForm()
    image_form = ProductImageForm()

    return render(request, 'users/manage_products.html', {
        'products': products,
        'filter_type': filter_type,
        'form': form,
        'image_form': image_form,
        'cart_item_count': get_cart_item_count(request.user),
    })

@manager_required
def add_product(request):
    """Ajouter un produit."""
    categories = Category.objects.filter(category_type='product', is_active=True)
    if not categories.exists():
        django_messages.warning(request, "Aucune catégorie de produit disponible. Veuillez en créer une avant d'ajouter un produit.")
        return redirect('users:manage_categories')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        image_form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            product = form.save(commit=False)
            product.is_active = True
            product.save()
            form.save_m2m()
            if image_form.cleaned_data['image']:  # Vérifier si une image a été uploadée
                image = image_form.save(commit=False)
                image.product = product
                image.save()
            django_messages.success(request, "Produit ajouté avec succès.")
            return redirect('users:manage_products')
    else:
        form = ProductForm()
        image_form = ProductImageForm()
    return render(request, 'users/add_product.html', {'form': form, 'image_form': image_form, 'cart_item_count': get_cart_item_count(request.user)})

@manager_required
def edit_product(request, product_id):
    """Modifier un produit existant."""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        image_form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            form.save()
            if image_form.cleaned_data['image']:
                # Supprimer les anciennes images si nécessaire
                product.images.all().delete()
                image = image_form.save(commit=False)
                image.product = product
                image.save()
            django_messages.success(request, "Produit mis à jour avec succès.")
            return redirect('users:manage_products')
    else:
        form = ProductForm(instance=product)
        image_form = ProductImageForm()
    return render(request, 'users/edit_product.html', {'form': form, 'image_form': image_form, 'product': product, 'cart_item_count': get_cart_item_count(request.user)})

# Gestion des commandes
@manager_required
def manage_orders(request):
    """Gérer les commandes (CRUD)."""
    orders = Order.objects.all().order_by('-created_at')  # Order by newest first
    return render(request, 'users/manage_orders.html', {
        'orders': orders,
        'cart_item_count': get_cart_item_count(request.user)
    })

def manager_update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()

            # Send email notification if the status is "delivered"
            if new_status == 'delivered':
                subject = "Votre commande a été livrée !"
                message = (
                    f"Bonjour {order.user.username},\n\n"
                    f"Nous sommes ravis de vous informer que votre commande (ID: {order.id}) "
                    f"a été livrée avec succès le {order.created_at.strftime('%d/%m/%Y à %H:%M')}.\n"
                    f"Montant total : {order.total_price} FCFA\n\n"
                    f"Merci d'avoir choisi Multifunction !\n"
                    f"Si vous avez des questions, n'hésitez pas à nous contacter à support@multifunction.com.\n\n"
                    f"Cordialement,\nL'équipe Multifunction"
                )
                recipient_email = order.user.email
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_email],
                    fail_silently=False,
                )

            django_messages.success(request, f"Statut de la commande {order.id} mis à jour avec succès.")
        else:
            django_messages.error(request, "Statut invalide.")
    return redirect('users:manage_orders')

@manager_required
def manager_delete_order(request, order_id):
    """Supprimer une commande."""
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.delete()
        django_messages.success(request, "Commande supprimée avec succès.")
    return redirect('users:manage_orders')

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        # Only allow cancellation if the order is in "pending" or "processing" status
        if order.status in ['pending', 'processing']:
            order.status = 'cancelled'
            order.save()
            django_messages.success(request, f"Votre commande {order.id} a été annulée avec succès.")
        else:
            django_messages.error(request, "Cette commande ne peut pas être annulée.")
    return redirect('users:orders')