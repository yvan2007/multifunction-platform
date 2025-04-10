from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem, Product, ProductImage, Category
from users.models import Favorite

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
    
    # Vérifier si le produit est dans les favoris de l'utilisateur
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = request.user.favorites.filter(id=product.id).exists()

    return render(request, 'ecommerce/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'is_favorited': is_favorited,
    })

@login_required
def add_product(request):
    from users.forms import ProductForm, ProductImageForm
    if not request.user.is_manager:
        messages.error(request, "Vous n'êtes pas autorisé à ajouter un produit.")
        return redirect('ecommerce:product_list')
    if request.method == 'POST':
        form = ProductForm(request.POST)
        image_form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            product = form.save()
            if image_form.cleaned_data['image']:
                image = image_form.save(commit=False)
                image.product = product
                image.save()
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
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    if not created:
        favorite.delete()
        messages.success(request, f"{product.name} retiré des favoris.")
    else:
        messages.success(request, f"{product.name} ajouté aux favoris !")
    return redirect(request.META.get('HTTP_REFERER', 'ecommerce:product_list'))

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