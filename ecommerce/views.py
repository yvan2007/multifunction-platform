# ecommerce/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem, Product, ProductImage, Category

def product_list(request):
    # Récupérer uniquement les catégories actives de type 'product'
    product_categories = Category.objects.filter(category_type='product', is_active=True)
    print("Categories:", product_categories)  # Débogage

    # Récupérer la catégorie sélectionnée (si un filtre est appliqué via GET)
    category_id = request.GET.get('category')
    if category_id:
        products = Product.objects.filter(category__id=category_id, is_active=True).order_by('-created_at')
        selected_category = get_object_or_404(Category, id=category_id, category_type='product')
    else:
        products = Product.objects.filter(is_active=True).order_by('-created_at')
        selected_category = None

    print("Products:", products)  # Débogage

    return render(request, 'ecommerce/product_list.html', {
        'product_categories': product_categories,
        'products': products,
        'selected_category': selected_category,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(slug=slug)[:4]
    return render(request, 'ecommerce/product_detail.html', {  # Correction du template
        'product': product,
        'related_products': related_products
    })

@login_required
def add_product(request):
    from multifunction_platform.forms import ProductForm
    if not request.user.is_manager:
        messages.error(request, "Vous n'êtes pas autorisé à ajouter un produit.")
        return redirect('ecommerce:product_list')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, "Produit ajouté avec succès !")
            return redirect('ecommerce:product_list')
    else:
        form = ProductForm()
    return render(request, 'ecommerce/add_product.html', {'form': form})

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