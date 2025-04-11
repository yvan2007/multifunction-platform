from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from orders.models import Order, OrderItem
from .models import Cart, CartItem, Product, ProductImage, Category, Review
from users.models import Favorite
from .forms import ProductForm, ProductImageForm, ReviewForm

def product_list(request):
    product_categories = Category.objects.filter(category_type='product', is_active=True)
    print("Categories in product_list:", [cat.name for cat in product_categories])  # Débogage

    category_id = request.GET.get('category')
    if category_id:
        products = Product.objects.filter(category__id=category_id, is_active=True).order_by('-created_at').prefetch_related('images')
        selected_category = get_object_or_404(Category, id=category_id, category_type='product')
    else:
        products = Product.objects.filter(is_active=True).order_by('-created_at').prefetch_related('images')
        selected_category = None

    print("Products in product_list:", [prod.name for prod in products])  # Débogage
    for product in products:
        print(f"Product: {product.name}, Category: {product.category.name}, Is Active: {product.is_active}, Primary Image: {product.primary_image.image.url if product.primary_image else 'None'}")

    return render(request, 'ecommerce/product_list.html', {
        'product_categories': product_categories,
        'products': products,
        'selected_category': selected_category,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(slug=slug)[:4]
    reviews = Review.objects.filter(product=product)
    
    # Vérifier si le produit est dans les favoris de l'utilisateur
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = request.user.favorites.filter(id=product.id).exists()

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(request, "Avis ajouté avec succès !")
            return redirect('ecommerce:product_detail', slug=slug)
    else:
        form = ReviewForm()

    return render(request, 'ecommerce/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'is_favorited': is_favorited,
        'reviews': reviews,
        'form': form,
    })

@login_required
def add_product(request):
    if not request.user.is_manager:
        messages.error(request, "Vous n'êtes pas autorisé à ajouter un produit.")
        return redirect('ecommerce:product_list')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        image_form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            product = form.save()
            if image_form.cleaned_data['image']:
                image = image_form.save(commit=False)
                image.product = product
                image.save()
            for image in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(product=product, image=image)
            messages.success(request, "Produit ajouté avec succès !")
            return redirect('ecommerce:product_list')
    else:
        form = ProductForm()
        image_form = ProductImageForm()
    return render(request, 'ecommerce/add_product.html', {'form': form, 'image_form': image_form})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"{product.name} a été ajouté à votre panier !")
    return redirect('orders:cart')

@login_required
def cart_detail(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return render(request, 'ecommerce/cart.html', {'cart': cart})
    else:
        messages.error(request, "Veuillez vous connecter pour voir votre panier.")
        return redirect('users:login')

@login_required
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    if not created:
        favorite.delete()
        messages.success(request, f"{product.name} retiré des favoris.")
    else:
        messages.success(request, f"{product.name} ajouté aux favoris !")
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'ecommerce:product_list')

def ecommerce(request):
    category_id = request.GET.get('category')
    categories = Category.objects.filter(category_type='product', is_active=True)
    print("Categories in ecommerce view:", [cat.name for cat in categories])  # Debug

    if category_id:
        products = Product.objects.filter(category_id=category_id, is_active=True).prefetch_related('images')
    else:
        products = Product.objects.filter(is_active=True).prefetch_related('images')
    
    print("Products in ecommerce view:", [prod.name for prod in products])  # Debug
    for product in products:
        print(f"Product: {product.name}, Category: {product.category.name}, Is Active: {product.is_active}, Primary Image: {product.primary_image.image.url if product.primary_image else 'None'}")
    
    return render(request, 'ecommerce/ecommerce.html', {
        'products': products,
        'categories': categories,
    })

@login_required
def checkout(request):
    # Récupérer le panier de l'utilisateur connecté
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        if not cart_items:
            messages.error(request, "Votre panier est vide.")
            return redirect('orders:cart')  # Vérifiez que 'orders:cart' existe
    except Cart.DoesNotExist:
        messages.error(request, "Votre panier est vide.")
        return redirect('orders:cart')

    if request.method == 'POST':
        # Calculer le prix total
        total_price = sum(item.product.price * item.quantity for item in cart_items)

        # Créer la commande
        order = Order.objects.create(user=request.user, total_price=total_price)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        # Envoyer un email de confirmation
        subject = 'Confirmation de votre commande'
        html_message = render_to_string('ecommerce/emails/order_confirmation.html', {
            'user': request.user,
            'order': order,
        })
        plain_message = strip_tags(html_message)
        from_email = 'kouayavana19@gmail.com'
        to_email = request.user.email
        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)

        # Vider le panier
        cart.items.all().delete()
        messages.success(request, "Votre commande a été passée avec succès !")
        return redirect('users:orders')  # Rediriger vers la page des commandes de l'utilisateur

    return render(request, 'ecommerce/checkout.html', {'cart': cart})
from django.shortcuts import render, get_object_or_404
from .models import Order

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'orders/order_confirmation.html', {'order': order})
