from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from ecommerce.models import Product, CartItem, Testimonial, Category, NewsletterSubscription
from blog.models import Article

# Utility function to calculate cart item count
def get_cart_item_count(user):
    """Calcule le nombre d'articles dans le panier de l'utilisateur."""
    if user.is_authenticated:
        return CartItem.objects.filter(cart__user=user).count()
    return 0

# Vues principales
def index(request):
    products = Product.objects.all()[:6]
    articles = Article.objects.filter(status='published')[:3]
    new_arrivals = Product.objects.order_by('-created_at')[:1]
    testimonials = Testimonial.objects.all()
    return render(request, 'multifunction_platform/index.html', {
        'products': products,
        'articles': articles,
        'new_arrivals': new_arrivals,
        'testimonials': testimonials,
        'cart_item_count': get_cart_item_count(request.user),
    })

def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'ecommerce/product_list.html', {
        'products': products,
        'query': query,
        'cart_item_count': get_cart_item_count(request.user),
    })

def about(request):
    return render(request, 'multifunction_platform/about.html', {
        'cart_item_count': get_cart_item_count(request.user),
    })

def privacy(request):
    return render(request, 'multifunction_platform/privacy.html', {
        'cart_item_count': get_cart_item_count(request.user),
    })

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Envoyer un email à l'administrateur
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail(
            subject=f"Message de {name} - {subject}",
            message=f"De : {email}\n\nMessage :\n{message}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        messages.success(request, "Votre message a été envoyé avec succès !")
        return redirect('contact')

    return render(request, 'multifunction_platform/contact.html', {
        'cart_item_count': get_cart_item_count(request.user),
    })

def testimonial(request):
    testimonials = Testimonial.objects.all()
    return render(request, 'multifunction_platform/testimonial.html', {
        'testimonials': testimonials,
        'cart_item_count': get_cart_item_count(request.user),
    })

def add_testimonial(request):
    from .forms import TestimonialForm
    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.user = request.user
            testimonial.save()
            messages.success(request, "Témoignage ajouté avec succès !")
            return redirect('testimonial')
    else:
        form = TestimonialForm()
    return render(request, 'multifunction_platform/add_testimonial.html', {
        'form': form,
        'cart_item_count': get_cart_item_count(request.user),
    })

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
    return render(request, 'multifunction_platform/subscribe_form.html', {
        'cart_item_count': get_cart_item_count(request.user),
    })