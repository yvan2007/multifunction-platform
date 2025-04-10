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

def remove_from_cart(request, product_id):
    if request.user.is_authenticated:
        # Utilisateur connecté : utiliser le modèle Cart
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        cart_item.delete()
        messages.success(request, "Produit retiré du panier !")
    else:
        # Utilisateur non connecté : utiliser la session
        if 'cart' in request.session:
            cart = request.session['cart']
            product_id_str = str(product_id)
            if product_id_str in cart:
                del cart[product_id_str]
                request.session['cart'] = cart
                request.session.modified = True
                messages.success(request, "Produit retiré du panier !")
            else:
                messages.error(request, "Ce produit n'est pas dans votre panier.")
        else:
            messages.error(request, "Votre panier est vide.")

    return redirect('orders:cart')

def cart(request):
    cart_items = []
    total_price = 0

    if request.user.is_authenticated:
        # Utilisateur connecté : utiliser le modèle Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()  # Récupérer les éléments via la relation related_name='items'
            total_price = cart.total_amount  # Utiliser la propriété total_amount du modèle Cart
        except Cart.DoesNotExist:
            cart_items = []
            total_price = 0
    else:
        # Utilisateur non connecté : utiliser la session
        if 'cart' in request.session:
            cart = request.session['cart']
            cart_items = []
            for product_id, quantity in cart.items():
                try:
                    product = Product.objects.get(id=int(product_id))
                    # Créer un objet temporaire pour simuler un CartItem
                    cart_item = type('CartItem', (), {
                        'product': product,
                        'quantity': quantity,
                        'get_total_price': lambda self: self.product.price * self.quantity
                    })()
                    cart_items.append(cart_item)
                    total_price += cart_item.get_total_price()
                except Product.DoesNotExist:
                    continue
        else:
            cart_items = []
            total_price = 0

    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'is_authenticated': request.user.is_authenticated,
        'total_price': total_price,
    })

@login_required(login_url='users:login')
def update_cart(request, product_id):  # Changed item_id to product_id
    """Mettre à jour la quantité d'un élément dans le panier."""
    if request.user.is_authenticated:
        # Utilisateur connecté : utiliser le modèle Cart
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        if request.method == 'POST':
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Quantité mise à jour !")
            else:
                cart_item.delete()
                messages.success(request, "Produit retiré du panier !")
    else:
        # Utilisateur non connecté : utiliser la session
        if 'cart' in request.session:
            cart = request.session['cart']
            product_id_str = str(product_id)
            if product_id_str in cart:
                quantity = int(request.POST.get('quantity', 1))
                if quantity > 0:
                    cart[product_id_str] = quantity
                    messages.success(request, "Quantité mise à jour !")
                else:
                    del cart[product_id_str]
                    messages.success(request, "Produit retiré du panier !")
                request.session['cart'] = cart
                request.session.modified = True
            else:
                messages.error(request, "Ce produit n'est pas dans votre panier.")
        else:
            messages.error(request, "Votre panier est vide.")

    return redirect('orders:cart')

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
            if not address_id:
                messages.error(request, "Veuillez sélectionner une adresse de livraison.")
                return redirect('orders:checkout')

            try:
                address = Address.objects.get(id=address_id, user=request.user)
            except Address.DoesNotExist:
                messages.error(request, "L'adresse sélectionnée est invalide ou n'existe plus. Veuillez en choisir une autre.")
                return redirect('orders:checkout')

            order = Order.objects.create(
                user=request.user,
                total_price=cart.total_amount,
                address=address  # Associer l'adresse à la commande
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

        return render(request, 'orders/checkout.html', {'cart': cart, 'addresses': addresses})
    else:
        # Cela ne devrait jamais arriver car @login_required redirige vers la page de connexion
        return redirect('users:login')

@login_required(login_url='users:login')
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})