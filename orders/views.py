### orders/views.py (version corrigée)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ecommerce.models import Cart, CartItem, Product, Order, OrderItem, Payment
from users.models import Address
import time

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        # Utilisateur connecté : utiliser le modèle Cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        # Utilisateur non connecté : utiliser la session
        if 'cart' not in request.session:
            request.session['cart'] = {}
        cart = request.session['cart']
        product_id_str = str(product_id)
        if product_id_str in cart:
            cart[product_id_str] += 1
        else:
            cart[product_id_str] = 1
        request.session['cart'] = cart
        request.session.modified = True  # S'assurer que la session est sauvegardée

    messages.success(request, "Produit ajouté au panier !")
    return redirect('orders:cart')

def cart(request):
    if request.user.is_authenticated:
        # Utilisateur connecté : utiliser le modèle Cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.all()
        total_amount = cart.total_amount
    else:
        # Utilisateur non connecté : utiliser la session
        if 'cart' not in request.session:
            request.session['cart'] = {}
        cart = request.session['cart']
        cart_items = []
        total_amount = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=int(product_id))
            total_price = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': total_price,
            })
            total_amount += total_price

    return render(request, 'ecommerce/cart_detail.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'is_authenticated': request.user.is_authenticated,
    })

@login_required(login_url='users:login')
def checkout(request):
    if request.user.is_authenticated:
        # Utilisateur connecté : utiliser le modèle Cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        if not cart.items.exists():
            messages.error(request, "Votre panier est vide.")
            return redirect('orders:cart')

        addresses = request.user.addresses.all()
        if not addresses:
            messages.error(request, "Veuillez ajouter une adresse avant de passer une commande.")
            return redirect('users:account_settings')

        if request.method == 'POST':
            address_id = request.POST.get('address_id')
            address = get_object_or_404(Address, id=address_id, user=request.user)
            order = Order.objects.create(
                user=request.user,
                total_price=cart.total_amount
            )
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
            Payment.objects.create(
                order=order,
                amount=order.total_price,
                payment_method='carte',
                transaction_id=str(time.time())
            )
            cart.items.all().delete()
            messages.success(request, "Commande passée avec succès !")
            return redirect('orders:order_history')

        return render(request, 'ecommerce/checkout.html', {'cart': cart, 'addresses': addresses})
    else:
        # Cela ne devrait jamais arriver car @login_required redirige vers la page de connexion
        return redirect('users:login')

@login_required(login_url='users:login')
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'ecommerce/order_history.html', {'orders': orders})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order

### orders/views.py (extrait)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ecommerce.models import Order, Product  # Changé pour importer depuis ecommerce.models
from .models import OrderItem  # Note : OrderItem ici est orders.OrderItem, ce qui peut poser problème

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})