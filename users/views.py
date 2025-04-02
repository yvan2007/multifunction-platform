from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.contrib import messages as django_messages
from .models import CustomUser, UserProfile, Address, Favorite, Message
from ecommerce.models import Product, Cart, CartItem
from orders.models import Order
from blog.models import Article, BlogCategory
from .forms import CustomAuthenticationForm, CustomUserCreationForm, ManagerCreationForm, UserProfileForm, AddressForm, ArticleForm, CategoryForm
import random
import string

# Utility function to check if user is a manager
def is_manager(user):
    return user.is_authenticated and user.is_manager

# Custom decorator for manager-only access
def manager_required(view_func):
    decorated_view_func = login_required(user_passes_test(is_manager)(view_func))
    return decorated_view_func

# Utility function to validate login credentials
def validate_login_credentials(request, form, is_manager_login=False):
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

# Login view for regular users (clients)
def login_view(request):
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
            return redirect(next_url)
    else:
        form = CustomAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})

# Login view for managers (with 2FA)
def manager_login_view(request):
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
                # Specify the backend explicitly
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                django_messages.success(request, "Connexion réussie !")
                del request.session['2fa_code']
                del request.session['user_id']
                return redirect('users:manager_dashboard')
            else:
                django_messages.error(request, "Code 2FA incorrect.")
                return render(request, 'users/manager_login_2fa.html')
        return render(request, 'users/manager_login_2fa.html')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        user, password = validate_login_credentials(request, form, is_manager_login=True)
        if user is not None:
            secret_code = form.cleaned_data.get('secret_code')
            if not secret_code:
                django_messages.error(request, "Le code secret est requis pour les gestionnaires.")
                return render(request, 'users/manager_login.html', {'form': form})
            if secret_code != user.secret_code:
                django_messages.error(request, "Code secret incorrect.")
                return render(request, 'users/manager_login.html', {'form': form})

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
                return render(request, 'users/manager_login.html', {'form': form})
            return render(request, 'users/manager_login_2fa.html')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'users/manager_login.html', {'form': form})

# Registration view
def register(request):
    user_type = request.GET.get('user_type', 'client')
    
    if user_type == 'manager':
        if request.method == 'POST':
            form = ManagerCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_manager = True
                user.generate_secret_code()  # Méthode supposée dans CustomUser pour générer un code secret
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
                    return render(request, 'users/register.html', {'form': form, 'user_type': user_type})
                user = form.save()
                UserProfile.objects.create(user=user)
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

    return render(request, 'users/register.html', {'form': form, 'user_type': user_type})

# Profile view
@login_required
def profile(request):
    return render(request, 'users/profile.html', {'user': request.user})

# Edit profile view
@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.username = request.POST.get('username')
        user.save()
        django_messages.success(request, 'Profil mis à jour avec succès.')
        return redirect('users:profile')
    return render(request, 'users/edit_profile.html', {'user': request.user})

# Account settings view
@login_required
def account_settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    addresses = request.user.addresses.all()

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=profile)
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
        profile_form = UserProfileForm(instance=profile)
        address_form = AddressForm()

    return render(request, 'users/account_settings.html', {
        'profile_form': profile_form,
        'address_form': address_form,
        'addresses': addresses,
    })

# Favorites view
@login_required
def favorites(request):
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
    return render(request, 'users/favorites.html', {'favorites': favorites})

# Messages view
@login_required
def user_messages(request): 
    sent_messages = request.user.sent_messages.all()
    received_messages = request.user.received_messages.all()
    return render(request, 'users/messages.html', {
        'sent_messages': sent_messages,
        'received_messages': received_messages,
    })

# Orders view
@login_required
def orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'users/orders.html', {'orders': orders})

# Manager Dashboard
@manager_required
def manager_dashboard(request):
    articles = Article.objects.all().count()
    categories = BlogCategory.objects.all().count()
    products = Product.objects.all().count()
    orders = Order.objects.all().count()
    
    context = {
        'article_count': articles,
        'category_count': categories,
        'product_count': products,
        'order_count': orders,
    }
    return render(request, 'users/manager_dashboard.html', context)

# Manage Articles with CRUD
@manager_required
def manage_articles(request):
    articles = Article.objects.all()
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            article_id = request.POST.get('article_id')
            article = get_object_or_404(Article, id=article_id)
            article.delete()
            django_messages.success(request, "Article supprimé avec succès.")
            return redirect('users:manage_articles')
        else:
            form = ArticleForm(request.POST)
            if form.is_valid():
                article = form.save(commit=False)
                article.author = request.user
                article.save()
                form.save_m2m()  # Save tags
                django_messages.success(request, "Article créé avec succès.")
                return redirect('users:manage_articles')
    else:
        form = ArticleForm()

    return render(request, 'users/manage_articles.html', {'articles': articles, 'form': form})

@manager_required
def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Article mis à jour avec succès.")
            return redirect('users:manage_articles')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'users/edit_article.html', {'form': form, 'article': article})

# Manage Categories with CRUD
@manager_required
def manage_categories(request):
    categories = BlogCategory.objects.all()
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            category_id = request.POST.get('category_id')
            category = get_object_or_404(BlogCategory, id=category_id)
            category.delete()
            django_messages.success(request, "Catégorie supprimée avec succès.")
            return redirect('users:manage_categories')
        else:
            form = CategoryForm(request.POST)
            if form.is_valid():
                form.save()
                django_messages.success(request, "Catégorie créée avec succès.")
                return redirect('users:manage_categories')
    else:
        form = CategoryForm()

    return render(request, 'users/manage_categories.html', {'categories': categories, 'form': form})

@manager_required
def edit_category(request, category_id):
    category = get_object_or_404(BlogCategory, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Catégorie mise à jour avec succès.")
            return redirect('users:manage_categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'users/edit_category.html', {'form': form, 'category': category})

@manager_required
def manage_products(request):
    products = Product.objects.all()
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            product.delete()
            django_messages.success(request, "Produit supprimé avec succès.")
            return redirect('users:manage_products')
        # Add logic for creating/editing products here if needed
    return render(request, 'users/manage_products.html', {'products': products})

@manager_required
def manage_orders(request):
    orders = Order.objects.all()
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            order_id = request.POST.get('order_id')
            order = get_object_or_404(Order, id=order_id)
            order.delete()
            django_messages.success(request, "Commande supprimée avec succès.")
            return redirect('users:manage_orders')
        # Add more actions (e.g., update status) here if needed
    return render(request, 'users/manage_orders.html', {'orders': orders})

# Custom Password Reset View
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.sites.shortcuts import get_current_site

class CustomPasswordResetView(PasswordResetView):
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

@manager_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Catégorie ajoutée avec succès.")
            return redirect('users:manage_categories')
    else:
        form = CategoryForm()
    return render(request, 'users/add_category.html', {'form': form})

@manager_required
def add_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user  # Set the current manager as the author
            article.save()
            django_messages.success(request, "Article ajouté avec succès.")
            return redirect('users:manage_articles')
    else:
        form = ArticleForm()
    return render(request, 'users/add_article.html', {'form': form})