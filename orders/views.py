from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from ecommerce.models import Product
from .models import Cart, CartItem, Order, OrderItem
from users.models import Address, CustomUser, Notification  # Ajout de Notification et CustomUser
import time

# Ajouter un produit au panier
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))  # Récupérer la quantité depuis le formulaire

    if request.user.is_authenticated:
        # Utilisateur connecté : utiliser le modèle Cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
    else:
        # Utilisateur non connecté : utiliser la session
        if 'cart' not in request.session:
            request.session['cart'] = {}
        cart = request.session['cart']
        product_id_str = str(product_id)
        if product_id_str in cart:
            cart[product_id_str] += quantity
        else:
            cart[product_id_str] = quantity
        request.session['cart'] = cart
        request.session.modified = True  # S'assurer que la session est sauvegardée

    messages.success(request, "Produit ajouté au panier !")
    return redirect('orders:cart')

# Retirer un produit du panier
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

# Afficher le panier
def cart(request):
    cart_items = []
    total_price = 0
    cart = None

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            # Get all cart items
            items = cart.items.all().select_related('product')
            # Filter out items with invalid products
            valid_items = []
            for item in items:
                try:
                    # Ensure the product exists
                    product = item.product
                    valid_items.append(item)
                    total_price += item.total_price
                except Product.DoesNotExist:
                    # Remove the invalid CartItem
                    item.delete()
                    continue
            cart_items = valid_items
        except Cart.DoesNotExist:
            cart_items = []
            total_price = 0
            cart = None
    else:
        if 'cart' in request.session:
            cart = request.session['cart']
            cart_items = []
            # Create a new session cart with only valid products
            new_cart = {}
            for product_id, quantity in cart.items():
                try:
                    product = Product.objects.get(id=int(product_id))
                    cart_item = type('CartItem', (), {
                        'product': product,
                        'quantity': quantity,
                        'total_price': product.price * quantity
                    })()
                    cart_items.append(cart_item)
                    total_price += cart_item.total_price
                    new_cart[product_id] = quantity
                except Product.DoesNotExist:
                    continue
            # Update the session with only valid products
            request.session['cart'] = new_cart
            request.session.modified = True
        else:
            cart_items = []
            total_price = 0

    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })

# Mettre à jour la quantité d'un produit dans le panier
@login_required(login_url='users:login')
def update_cart(request, product_id):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Quantité mise à jour !")
        else:
            cart_item.delete()
            messages.success(request, "Produit retiré du panier !")
    return redirect('orders:cart')

# Passer la commande
@login_required(login_url='users:login')
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all().select_related('product')
        if not cart_items:
            messages.error(request, "Votre panier est vide.")
            return redirect('orders:cart')
    except Cart.DoesNotExist:
        messages.error(request, "Votre panier est vide.")
        return redirect('orders:cart')

    # Récupérer les adresses de l'utilisateur
    addresses = Address.objects.filter(user=request.user)

    # Calculer le sous-total
    subtotal = sum(item.total_price for item in cart_items)

    # Frais de livraison
    BASE_DELIVERY_COST = 2000  # Frais de base
    COD_FEE = 500  # Frais supplémentaires pour paiement à la livraison

    # Définir la méthode de paiement par défaut
    payment_method = request.POST.get('payment_method', 'cod') if request.method == 'POST' else 'cod'

    # Calculer les frais de livraison
    delivery_cost = BASE_DELIVERY_COST
    if payment_method == 'cod':
        delivery_cost += COD_FEE

    # Calculer le total final
    total_price = subtotal + delivery_cost

    # Créer un objet cart pour le template
    cart_obj = type('Cart', (), {
        'items': cart_items,
        'total_amount': subtotal
    })()

    if request.method == 'POST':
        # Récupérer l'adresse sélectionnée
        address_id = request.POST.get('address_id')
        if not address_id:
            messages.error(request, "Veuillez sélectionner une adresse de livraison.")
            return redirect('orders:checkout')

        address = get_object_or_404(Address, id=address_id, user=request.user)

        # Récupérer les détails de la carte si le paiement est par carte
        card_number = request.POST.get('card_number', '') if payment_method == 'card' else ''
        card_expiry = request.POST.get('card_expiry', '') if payment_method == 'card' else ''
        card_cvv = request.POST.get('card_cvv', '') if payment_method == 'card' else ''
        card_holder = request.POST.get('card_holder', '') if payment_method == 'card' else ''

        # Récupérer le numéro de téléphone si le paiement est par Orange Money ou Wave
        phone_number = request.POST.get('phone_number', '') if payment_method in ['orange_money', 'mtn_money'] else ''

        # Valider les détails de la carte si le paiement est par carte
        if payment_method == 'card':
            if not (card_number and card_expiry and card_cvv and card_holder):
                messages.error(request, "Veuillez remplir tous les champs de la carte bancaire.")
                return redirect('orders:checkout')
            # Basic validation (you should integrate a payment gateway for real validation)
            if not card_number.replace(' ', '').isdigit() or len(card_number.replace(' ', '')) < 16:
                messages.error(request, "Numéro de carte invalide.")
                return redirect('orders:checkout')
            if not card_expiry or len(card_expiry) != 5 or card_expiry[2] != '/':
                messages.error(request, "Date d'expiration invalide (format: MM/AA).")
                return redirect('orders:checkout')
            if not card_cvv.isdigit() or len(card_cvv) < 3:
                messages.error(request, "CVV invalide.")
                return redirect('orders:checkout')

        # Valider le numéro de téléphone si le paiement est par Orange Money ou Wave
        if payment_method in ['orange_money', 'mtn_money']:
            if not phone_number:
                messages.error(request, "Veuillez entrer un numéro de téléphone pour le paiement mobile.")
                return redirect('orders:checkout')
            # Basic validation for phone number
            if not phone_number.startswith('+') or len(phone_number.replace(' ', '')) < 10:
                messages.error(request, "Numéro de téléphone invalide (ex: +225 01 23 45 67 89).")
                return redirect('orders:checkout')

        # Créer la commande
        order = Order.objects.create(
            user=request.user,
            address=address,
            total_price=total_price,
            payment_method=payment_method,
            delivery_cost=delivery_cost,
            status='pending',
            card_number=card_number,
            card_expiry=card_expiry,
            card_cvv=card_cvv,
            card_holder=card_holder,
            phone_number=phone_number,
        )

        # Ajouter les éléments du panier à la commande
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        # Envoyer un email de confirmation
        context = {
            'user': request.user,
            'order': order,
            'request': request,
        }
        html_content = render_to_string('ecommerce/emails/order_confirmation.html', context)
        send_mail(
            subject='Confirmation de votre commande',
            message='Merci pour votre commande ! Voici les détails.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[request.user.email],
            html_message=html_content,
            fail_silently=False,
        )

        # Vider le panier
        cart.items.all().delete()
        messages.success(request, "Commande passée avec succès ! Un email de confirmation vous a été envoyé.")
        return redirect('orders:order_confirmation', order_id=order.id)

    return render(request, 'orders/checkout.html', {
        'cart': cart_obj,  # Passer l'objet cart pour le récapitulatif
        'addresses': addresses,
    })

# Historique des commandes
@login_required(login_url='users:login')
def order_history(request):
    orders = Order.objects.filter(user=request.user).select_related('address').prefetch_related('items__product').order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})

# Détails d'une commande
@login_required(login_url='users:login')
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related('address').prefetch_related('items__product'), id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

# Page de confirmation de commande
@login_required(login_url='users:login')
def order_confirmation(request, order_id):
    order = get_object_or_404(Order.objects.select_related('address').prefetch_related('items__product'), id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})

def simulate_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    status_sequence = ['pending', 'processing', 'shipped', 'delivered']

    for status in status_sequence:
        order.status = status
        order.save()
        messages.success(request, f"Statut mis à jour : {status}")
        time.sleep(5)  # Attendre 5 secondes entre chaque changement

    return redirect('orders:order_detail', order_id=order.id)

@login_required(login_url='users:login')
def create_order(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        messages.error(request, "Votre panier est vide.")
        return redirect('ecommerce:cart')

    # Créer une nouvelle commande
    order = Order.objects.create(user=request.user, total_price=cart.get_total_price())
    for item in cart.items.all():
        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
    
    # Vider le panier après la commande
    cart.items.all().delete()

    # Créer une notification pour tous les gestionnaires
    managers = CustomUser.objects.filter(is_manager=True)
    for manager in managers:
        Notification.objects.create(
            user=manager,
            notification_type='new_order',
            message=f"Nouvelle commande #{order.id} passée par {request.user.username}."
        )

    # Créer une notification pour le client (détails de la commande)
    Notification.objects.create(
        user=request.user,
        notification_type='order_details',
        message=f"Les détails de votre commande #{order.id} ont été envoyés à votre email."
    )

    # Envoyer un email au client avec les détails de la commande
    subject = f"Détails de votre commande #{order.id}"
    message = (
        f"Bonjour {request.user.username},\n\n"
        f"Merci pour votre commande ! Voici les détails :\n"
        f"Commande ID : {order.id}\n"
        f"Montant total : {order.total_price} FCFA\n"
        f"Articles :\n"
        f"\n".join([f"- {item.product.name} (x{item.quantity}) : {item.price} FCFA" for item in order.items.all()]) +
        f"\n\nMerci d'avoir choisi Multifunction !"
    )  # Ajout de la parenthèse fermante
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email],
        fail_silently=False,
    )

    messages.success(request, "Commande passée avec succès !")
    return redirect('users:orders')