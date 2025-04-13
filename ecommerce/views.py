# ecommerce/views.py
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
from django.db import transaction  # Pour gérer les transactions atomiques

from orders.models import Order, OrderItem
from .models import Cart, CartItem, Product, ProductImage, Category, Review
from users.models import Favorite
from .forms import ProductForm, ProductImageForm, ReviewForm

def product_list(request):
    product_categories = Category.objects.filter(category_type='product', is_active=True)
    print("Categories in product_list:", [cat.name for cat in product_categories])  # Débogage

    category_name = request.GET.get('category')
    if category_name:
        products = Product.objects.filter(category__name=category_name, is_active=True).order_by('-created_at').prefetch_related('images')
        selected_category = get_object_or_404(Category, name=category_name, category_type='product')
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
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(slug=slug)[:4]
    reviews = Review.objects.filter(product=product)
    
    # Vérifier si le produit est dans les favoris de l'utilisateur
    is_favorited = False
    has_ordered = False
    has_reviewed = False

    if request.user.is_authenticated:
        is_favorited = request.user.favorites.filter(product=product).exists()
        # Vérifier si l'utilisateur a commandé ce produit
        has_ordered = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='completed'
        ).exists()
        # Vérifier si l'utilisateur a déjà laissé un avis
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Ce produit n\'est plus disponible.'
            }, status=400)
        messages.error(request, "Ce produit n'est plus disponible.")
        return redirect('ecommerce:product_list')

    # Vérifier le stock avant d'ajouter au panier
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        # Si l'article est déjà dans le panier, vérifier si on peut augmenter la quantité
        requested_quantity = cart_item.quantity + 1
        if requested_quantity > product.stock:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Stock insuffisant pour ajouter plus de ce produit.'
                }, status=400)
            messages.error(request, "Stock insuffisant pour ajouter plus de ce produit.")
            return redirect('orders:cart')
        cart_item.quantity = requested_quantity
        cart_item.save()
    else:
        # Si nouvel article, vérifier que le stock est suffisant
        if product.stock < 1:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Ce produit est en rupture de stock.'
                }, status=400)
            messages.error(request, "Ce produit est en rupture de stock.")
            return redirect('ecommerce:product_list')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{product.name} a été ajouté à votre panier !"
        })
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
    if not product.is_active:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Ce produit n\'est plus disponible.'
            }, status=400)
        messages.error(request, "Ce produit n'est plus disponible.")
        return redirect('ecommerce:product_detail', slug=product.slug)

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

    print(f"Category Name from GET: {category_name}")
    print(f"Sort: {sort}, Search: {search}, Min Price: {min_price}, Max Price: {max_price}, In Stock: {in_stock}")

    categories = Category.objects.filter(category_type='product', is_active=True)
    category_names = [unicodedata.normalize('NFC', cat.name) for cat in categories]
    print("Categories (normalized):", category_names)
    
    if category_name:
        try:
            decoded_category_name = urllib.parse.unquote(category_name)
            normalized_category_name = unicodedata.normalize('NFC', decoded_category_name)
            print(f"Decoded and Normalized Category Name: {normalized_category_name}")

            if normalized_category_name not in category_names:
                print(f"Category {normalized_category_name} not found in normalized category names.")
                products = Product.objects.none()
                selected_category = None
            else:
                selected_category = get_object_or_404(Category, name=normalized_category_name, category_type='product')
                products = Product.objects.filter(category=selected_category, is_active=True).prefetch_related('images')
                print(f"Products for category {normalized_category_name}:", [prod.name for prod in products])
        except Category.DoesNotExist:
            print(f"Category {normalized_category_name} not found.")
            products = Product.objects.none()
            selected_category = None
        except Exception as e:
            print(f"Error filtering products for category {normalized_category_name}: {str(e)}")
            products = Product.objects.none()
            selected_category = None
    else:
        products = Product.objects.filter(is_active=True).prefetch_related('images')
        selected_category = None
        print("All products:", [prod.name for prod in products])

    if search:
        products = products.filter(name__icontains=search)
        print("Products after search filter:", [prod.name for prod in products])

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
            print("Products after min price filter:", [prod.name for prod in products])
        except (ValueError, TypeError) as e:
            print(f"Error applying min price filter: {str(e)}")

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
            print("Products after max price filter:", [prod.name for prod in products])
        except (ValueError, TypeError) as e:
            print(f"Error applying max price filter: {str(e)}")

    if in_stock == 'true':
        products = products.filter(stock__gt=0)
        print("Products after in stock filter:", [prod.name for prod in products])

    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'date_desc':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')
    print("Products after sorting:", [prod.name for prod in products])

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    print(f"Page {page_number}, Has Next: {page_obj.has_next()}")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            html = render_to_string('ecommerce/product_list_partial.html', {
                'products': page_obj,
                'request': request,
            })
            print("HTML rendered successfully for AJAX request")
            return JsonResponse({
                'html': html,
                'has_next': page_obj.has_next(),
            })
        except Exception as e:
            print(f"Error rendering template for AJAX: {str(e)}")
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
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        if not cart_items:
            messages.error(request, "Votre panier est vide.")
            return redirect('orders:cart')
    except Cart.DoesNotExist:
        messages.error(request, "Votre panier est vide.")
        return redirect('orders:cart')

    # Calculer les sous-totaux pour chaque article
    for item in cart_items:
        item.subtotal = item.product.price * item.quantity

    # Calculer le prix total
    total_price = sum(item.subtotal for item in cart_items)

    if request.method == 'POST':
        # Vérifier les champs du formulaire
        country = request.POST.get('country')
        city = request.POST.get('city')
        if not country or not city:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('ecommerce:checkout')

        # Vérifier le stock avant de créer la commande
        insufficient_stock_items = []
        for item in cart_items:
            if item.quantity > item.product.stock:
                insufficient_stock_items.append(f"{item.product.name} (demandé: {item.quantity}, disponible: {item.product.stock})")

        if insufficient_stock_items:
            messages.error(request, f"Stock insuffisant pour les produits suivants : {', '.join(insufficient_stock_items)}")
            return redirect('orders:cart')

        # Utiliser une transaction pour garantir l'intégrité des données
        with transaction.atomic():
            # Créer la commande
            order = Order.objects.create(
                user=request.user,
                total_price=total_price,
                country=country,
                city=city,
                status='pending'
            )

            # Créer les éléments de la commande et diminuer le stock
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                # Diminuer le stock du produit
                item.product.stock -= item.quantity
                item.product.save()

            # Envoyer un email de confirmation
            subject = 'Confirmation de votre commande'
            html_message = render_to_string('ecommerce/emails/order_confirmation.html', {
                'user': request.user,
                'order': order,
            })
            plain_message = strip_tags(html_message)
            from_email = 'kouayavana19@gmail.com'
            to_email = request.user.email
            send_mail(subject, plain_message, from_email, [to_email], html_message=html_message, fail_silently=False)

            # Vider le panier
            cart.items.all().delete()
            messages.success(request, "Votre commande a été passée avec succès !")
            return redirect('users:orders')

    return render(request, 'ecommerce/checkout.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    })

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})

def promotions(request):
    promoted_products = Product.objects.filter(discount__gt=0, is_active=True).order_by('-created_at')
    return render(request, 'ecommerce/promotions.html', {
        'products': promoted_products,
        'cart_item_count': get_cart_item_count(request.user),
    })

def get_cart_item_count(user):
    if user.is_authenticated:
        return CartItem.objects.filter(cart__user=user).count()
    return 0