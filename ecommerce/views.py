from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import JsonResponse
from django.core.paginator import Paginator
import unicodedata
import urllib.parse
from django.db import transaction
from django.conf import settings

from orders.models import Order, OrderItem
from users.models import Address
from .models import Cart, CartItem, Product, ProductImage, Category, Review
from users.models import Favorite
from .forms import ProductForm, ProductImageForm, ReviewForm

def product_list(request):
    product_categories = Category.objects.filter(category_type='product', is_active=True)
    category_name = request.GET.get('category')
    if category_name:
        products = Product.objects.filter(category__name=category_name, is_active=True).order_by('-created_at').prefetch_related('images')
        selected_category = get_object_or_404(Category, name=category_name, category_type='product')
    else:
        products = Product.objects.filter(is_active=True).order_by('-created_at').prefetch_related('images')
        selected_category = None

    return render(request, 'ecommerce/product_list.html', {
        'product_categories': product_categories,
        'products': products,
        'selected_category': selected_category,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(slug=slug)[:4]
    reviews = Review.objects.filter(product=product)
    
    is_favorited = False
    has_ordered = False
    has_reviewed = False

    if request.user.is_authenticated:
        is_favorited = request.user.favorites.filter(product=product).exists()
        has_ordered = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='completed'
        ).exists()
        has_reviewed = request.user.reviews.filter(product=product).exists()

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            if has_reviewed:
                messages.error(request, "Vous avez déjà laissé un avis pour ce produit.")
                return redirect('ecommerce:product_detail', slug=slug)
            if not has_ordered:
                messages.error(request, "Vous devez avoir commandé ce produit pour laisser un avis.")
                return redirect('ecommerce:product_detail', slug=slug)
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
        'has_ordered': has_ordered,
        'has_reviewed': has_reviewed,
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
    if not product.is_active:
        messages.error(request, "Ce produit n'est plus disponible.")
        return JsonResponse({'success': False, 'message': "Ce produit n'est plus disponible."}, status=400)

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
    else:
        quantity = 1

    requested_quantity = cart_item.quantity + quantity if not created else quantity
    if requested_quantity > product.stock:
        messages.error(request, f"Stock insuffisant pour {product.name} (disponible : {product.stock}).")
        return JsonResponse({'success': False, 'message': f"Stock insuffisant pour {product.name} (disponible : {product.stock})."}, status=400)

    cart_item.quantity = requested_quantity
    cart_item.save()
    cart_count = cart.items.count()

    messages.success(request, f"{product.name} a été ajouté à votre panier !")
    return JsonResponse({
        'success': True,
        'message': f"{product.name} a été ajouté à votre panier !",
        'cart_count': cart_count
    })

@login_required
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all().select_related('product')  # Optimisation avec select_related
        if not cart_items:
            messages.info(request, "Votre panier est vide.")
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        cart_items = []
        messages.info(request, "Votre panier est vide.")

    # Calcul des sous-totaux pour chaque article
    for item in cart_items:
        item.subtotal = item.product.discounted_price * item.quantity

    # Calcul du total
    subtotal = sum(item.subtotal for item in cart_items)
    delivery_cost = 2000 if cart_items else 0  # Frais de livraison fixes si panier non vide
    total_price = subtotal + delivery_cost

    return render(request, 'ecommerce/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_cost': delivery_cost,
        'total_price': total_price,
    })

@login_required
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not product.is_active:
        messages.error(request, "Ce produit n'est plus disponible.")
        return JsonResponse({'success': False, 'message': "Ce produit n'est plus disponible."}, status=400)

    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    if not created:
        favorite.delete()
        message = f"{product.name} retiré des favoris."
        is_favorited = False
    else:
        message = f"{product.name} ajouté aux favoris !"
        is_favorited = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited,
            'message': message
        })
    messages.success(request, message)
    return redirect('ecommerce:product_detail', slug=product.slug)

def ecommerce(request):
    category_name = request.GET.get('category')
    sort = request.GET.get('sort', 'default')
    search = request.GET.get('search', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    in_stock = request.GET.get('in_stock', '')

    categories = Category.objects.filter(category_type='product', is_active=True)
    category_names = [unicodedata.normalize('NFC', cat.name) for cat in categories]
    
    if category_name:
        try:
            decoded_category_name = urllib.parse.unquote(category_name)
            normalized_category_name = unicodedata.normalize('NFC', decoded_category_name)
            if normalized_category_name not in category_names:
                products = Product.objects.none()
                selected_category = None
            else:
                selected_category = get_object_or_404(Category, name=normalized_category_name, category_type='product')
                products = Product.objects.filter(category=selected_category, is_active=True).prefetch_related('images')
        except Category.DoesNotExist:
            products = Product.objects.none()
            selected_category = None
        except Exception as e:
            products = Product.objects.none()
            selected_category = None
    else:
        products = Product.objects.filter(is_active=True).prefetch_related('images')
        selected_category = None

    if search:
        products = products.filter(name__icontains=search)

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    if in_stock == 'true':
        products = products.filter(stock__gt=0)

    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'date_desc':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            html = render_to_string('ecommerce/product_list_partial.html', {
                'products': page_obj,
                'request': request,
            })
            return JsonResponse({
                'html': html,
                'has_next': page_obj.has_next(),
            })
        except Exception as e:
            return JsonResponse({
                'error': 'Une erreur est survenue lors du rendu des produits.'
            }, status=500)

    return render(request, 'ecommerce/ecommerce.html', {
        'products': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
    })

@login_required
def checkout(request):
    print("Checkout view loaded")  # Debug print to confirm file usage
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        if not cart_items:
            messages.error(request, "Votre panier est vide.")
            return redirect('ecommerce:cart_detail')
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        cart_items = []

    for item in cart_items:
        item.subtotal = item.product.price * item.quantity

    total_price = sum(item.subtotal for item in cart_items)
    addresses = Address.objects.filter(user=request.user)

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')

        if not address_id or not payment_method:
            messages.error(request, "Veuillez sélectionner une adresse et une méthode de paiement.")
            return redirect('ecommerce:checkout')

        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            messages.error(request, "Adresse invalide.")
            return redirect('ecommerce:checkout')

        insufficient_stock_items = []
        for item in cart_items:
            if item.quantity > item.product.stock:
                insufficient_stock_items.append(f"{item.product.name} (demandé: {item.quantity}, disponible: {item.product.stock})")

        if insufficient_stock_items:
            messages.error(request, f"Stock insuffisant pour les produits suivants : {', '.join(insufficient_stock_items)}")
            return redirect('ecommerce:cart_detail')

        with transaction.atomic():
            # Créer la commande
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_price=total_price,
                payment_method=payment_method,
                status='pending'
            )

            # Créer les OrderItem et décrémenter le stock
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                # Décrémenter le stock
                item.product.stock -= item.quantity
                if item.product.stock < 0:  # Sécurité supplémentaire
                    raise ValueError(f"Stock négatif pour {item.product.name}")
                item.product.save()

            # Envoyer l'email de confirmation
            subject = 'Confirmation de votre commande'
            html_message = render_to_string('ecommerce/emails/order_confirmation.html', {
                'user': request.user,
                'order': order,
                'request': request,  # Ajouté pour les URLs absolues dans l'email
            })
            plain_message = strip_tags(html_message)
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = request.user.email
            send_mail(subject, plain_message, from_email, [to_email], html_message=html_message, fail_silently=False)

            # Vider le panier
            cart.items.all().delete()
            messages.success(request, "Votre commande a été passée avec succès !")
            return redirect('orders:order_confirmation', order_id=order.id)

    return render(request, 'ecommerce/checkout.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'addresses': addresses,
    })

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})

def promotions(request):
    promoted_products = Product.objects.filter(discount__gt=0, is_active=True).order_by('-created_at')
    return render(request, 'ecommerce/promotions.html', {'products': promoted_products})


@login_required
def update_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product=product)
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Panier introuvable."}, status=400)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            cart_item.delete()
            return JsonResponse({'success': True, 'message': f"{product.name} retiré du panier."})
        if quantity > product.stock:
            return JsonResponse({'success': False, 'message': f"Stock insuffisant pour {product.name} (disponible : {product.stock})."}, status=400)
        
        cart_item.quantity = quantity
        cart_item.save()
        return JsonResponse({'success': True, 'message': f"Quantité mise à jour pour {product.name}."})
    return JsonResponse({'success': False, 'message': "Méthode non autorisée."}, status=400)

@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product=product)
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Panier introuvable."}, status=400)

    if request.method == 'POST':
        cart_item.delete()
        return JsonResponse({'success': True, 'message': f"{product.name} retiré du panier."})
    return JsonResponse({'success': False, 'message': "Méthode non autorisée."}, status=400)