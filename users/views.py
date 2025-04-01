from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.contrib import messages
from .models import CustomUser, UserProfile, Address, Favorite, Message
from ecommerce.models import Product, Cart, CartItem
from orders.models import Order
from .forms import CustomAuthenticationForm, CustomUserCreationForm, ManagerCreationForm, UserProfileForm, AddressForm
import random
import string

# Utility function to check if user is a manager
def is_manager(user):
    return user.is_authenticated and user.is_manager

# Utility function to validate login credentials
def validate_login_credentials(request, form, is_manager_login=False):
    from django.contrib import messages
    from django.db.models import Q
    from .models import CustomUser

    if not form.is_valid():
        messages.error(request, "Erreur lors de la connexion. Veuillez vérifier les champs.")
        return None, None

    login_field = form.cleaned_data.get('username')
    password = form.cleaned_data.get('password')
    print(f"Validation - login_field: {login_field}, password: {password}")

    if not login_field or not password:
        messages.error(request, "Le nom d'utilisateur/email et le mot de passe sont requis.")
        return None, None

    try:
        user = CustomUser.objects.get(Q(username=login_field) | Q(email=login_field))
        user = authenticate(request, username=user.username, password=password)
    except CustomUser.DoesNotExist:
        user = None

    print("Résultat authenticate:", user)
    if user is None:
        messages.error(request, "Nom d'utilisateur/email ou mot de passe incorrect.")
        return None, None

    if is_manager_login and not user.is_manager:
        messages.error(request, "Vous n'êtes pas un gestionnaire. Utilisez la page de connexion client (/users/login/).")
        return None, None
    elif not is_manager_login and user.is_manager:
        messages.error(request, "Les gestionnaires doivent utiliser la page de connexion dédiée (/users/manager-login/).")
        return None, None

    return user, password

# Login view for regular users (clients)
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_manager:
            return redirect('manager_dashboard')
        return redirect('index')

    if request.method == 'POST':
        print("Données POST brutes:", request.POST)
        form = CustomAuthenticationForm(request, data=request.POST)
        print("Formulaire valide ?", form.is_valid())
        if form.is_valid():
            print("Données nettoyées:", form.cleaned_data)
        else:
            print("Erreurs du formulaire:", form.errors)  # Affiche les erreurs pour déboguer
        user, _ = validate_login_credentials(request, form, is_manager_login=False)
        print("Utilisateur après validation:", user)
        if user is not None:
            login(request, user)
            # Transfert du panier de la session vers l'utilisateur connecté
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
            messages.success(request, "Connexion réussie !")
            return redirect(next_url)
        else:
            print("Échec de la connexion")
    else:
        form = CustomAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})

# Login view for managers (with 2FA)
def manager_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_manager:
            return redirect('manager_dashboard')
        else:
            messages.error(request, "Vous n'êtes pas autorisé à accéder à cette page.")
            return redirect('index')

    if '2fa_code' in request.session:
        if request.method == 'POST':
            entered_code = request.POST.get('2fa_code')
            if entered_code == request.session['2fa_code']:
                user = CustomUser.objects.get(id=request.session['user_id'])
                login(request, user)
                messages.success(request, "Connexion réussie !")
                del request.session['2fa_code']
                del request.session['user_id']
                return redirect('manager_dashboard')
            else:
                messages.error(request, "Code 2FA incorrect.")
                return render(request, 'users/manager_login_2fa.html')
        return render(request, 'users/manager_login_2fa.html')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        user, password = validate_login_credentials(request, form, is_manager_login=True)
        if user is not None:
            secret_code = form.cleaned_data.get('secret_code')
            if not secret_code:
                messages.error(request, "Le code secret est requis pour les gestionnaires.")
                return render(request, 'users/manager_login.html', {'form': form})
            if secret_code != user.secret_code:
                messages.error(request, "Code secret incorrect.")
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
                messages.info(request, "Un code de vérification a été envoyé à votre email.")
            except Exception as e:
                messages.error(request, "Erreur lors de l'envoi du code 2FA. Veuillez réessayer plus tard.")
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
                user.generate_secret_code()
                user.save()
                try:
                    send_mail(
                        subject='Votre code secret pour la connexion gestionnaire',
                        message=f"Votre code secret est : {user.secret_code}",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    messages.success(request, "Inscription réussie ! Vérifiez votre email pour le code secret.")
                except Exception as e:
                    messages.error(request, "Inscription réussie, mais erreur lors de l'envoi du code secret. Contactez l'administrateur.")
                return redirect('users:login')
            else:
                if 'username' in form.errors:
                    messages.error(request, "Ce nom d'utilisateur est déjà pris.")
                if 'email' in form.errors:
                    messages.error(request, "Cet email est déjà utilisé.")
                if 'password2' in form.errors:
                    messages.error(request, "Les mots de passe ne correspondent pas.")
                messages.error(request, "Erreur lors de l'inscription. Veuillez vérifier les champs.")
        else:
            form = ManagerCreationForm()
    else:
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                if CustomUser.objects.filter(username=username).exists():
                    messages.error(request, "Ce nom d'utilisateur est déjà pris.")
                    return render(request, 'users/register.html', {'form': form, 'user_type': user_type})
                user = form.save()
                UserProfile.objects.create(user=user)
                password = form.cleaned_data.get('password1')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, "Inscription réussie ! Vous êtes maintenant connecté.")
                    return redirect('index')
                else:
                    messages.error(request, "Erreur lors de la connexion automatique. Veuillez vous connecter manuellement.")
                    return redirect('users:login')
            else:
                if 'username' in form.errors:
                    messages.error(request, "Ce nom d'utilisateur est déjà pris.")
                if 'email' in form.errors:
                    messages.error(request, "Cet email est déjà utilisé.")
                if 'password2' in form.errors:
                    messages.error(request, "Les mots de passe ne correspondent pas.")
                messages.error(request, "Erreur lors de l'inscription. Veuillez vérifier les champs.")
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
        messages.success(request, 'Profil mis à jour avec succès.')
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
            messages.success(request, "Profil mis à jour avec succès !")
        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Adresse ajoutée avec succès !")
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
            messages.success(request, f"{product.name} ajouté aux favoris !")
        elif action == 'remove':
            Favorite.objects.filter(user=request.user, product=product).delete()
            messages.success(request, f"{product.name} retiré des favoris !")
        return redirect('users:favorites')
    return render(request, 'users/favorites.html', {'favorites': favorites})

# Messages view
@login_required
def messages(request):
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

# Custom Password Reset View
from django.contrib.auth.views import PasswordResetView
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