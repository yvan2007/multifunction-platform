from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from ecommerce.models import Product
from .models import Cart, CartItem, Order, OrderItem
from users.models import Address, CustomUser, Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.db import transaction
import time

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not product.is_active:
        messages.error(request, "Ce produit n'est plus disponible.")
        return redirect('ecommerce:product_detail', slug=product.slug)

    quantity = int(request.POST.get('quantity', 1))
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    requested_quantity = cart_item.quantity + quantity if not created else quantity
    if requested_quantity > product.stock:
        messages.error(request, f"Stock insuffisant pour {product.name} (disponible : {product.stock}).")
        return redirect('ecommerce:product_detail', slug=product.slug)

    cart_item.quantity = requested_quantity
    cart_item.save()
    messages.success(request, f"{product.name} a été ajouté à votre panier !")
    return redirect('ecommerce:cart_detail')

@login_required
def remove_from_cart(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f"{product_name} a été supprimé du panier.")
    return JsonResponse({'success': True, 'message': f'{product_name} a été supprimé du panier.'})

@login_required
def update_cart(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f"{product_name} a été supprimé du panier.")
        return JsonResponse({'success': True, 'message': f'{product_name} a été supprimé du panier.'})
    elif quantity > product.stock:
        messages.error(request, f"Stock insuffisant pour {product.name} (disponible : {product.stock}).")
        return JsonResponse({'success': False, 'message': f'Stock insuffisant pour {product.name} (disponible : {product.stock}).'}, status=400)
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"Quantité de {product.name} mise à jour.")
        return JsonResponse({'success': True, 'message': f'Quantité de {product.name} mise à jour.'})

@login_required(login_url='users:login')
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all().select_related('product')
        if not cart_items:
            messages.error(request, "Votre panier est vide.")
            return redirect('ecommerce:cart_detail')
    except Cart.DoesNotExist:
        messages.error(request, "Votre panier est vide.")
        return redirect('ecommerce:cart_detail')

    addresses = Address.objects.filter(user=request.user)
    subtotal = sum(item.product.discounted_price * item.quantity for item in cart_items)
    BASE_DELIVERY_COST = 2000
    COD_FEE = 500
    payment_method = request.POST.get('payment_method', 'cod') if request.method == 'POST' else 'cod'
    delivery_cost = BASE_DELIVERY_COST
    if payment_method == 'cod':
        delivery_cost += COD_FEE
    total_price = subtotal + delivery_cost

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if not address_id:
            messages.error(request, "Veuillez sélectionner une adresse de livraison.")
            return redirect('ecommerce:checkout')

        address = get_object_or_404(Address, id=address_id, user=request.user)
        card_number = request.POST.get('card_number', '') if payment_method == 'card' else ''
        card_expiry = request.POST.get('card_expiry', '') if payment_method == 'card' else ''
        card_cvv = request.POST.get('card_cvv', '') if payment_method == 'card' else ''
        card_holder = request.POST.get('card_holder', '') if payment_method == 'card' else ''
        phone_number = request.POST.get('phone_number', '') if payment_method in ['orange_money', 'mtn_money'] else ''

        if payment_method == 'card':
            if not (card_number and card_expiry and card_cvv and card_holder):
                messages.error(request, "Veuillez remplir tous les champs de la carte bancaire.")
                return redirect('ecommerce:checkout')
            if not card_number.replace(' ', '').isdigit() or len(card_number.replace(' ', '')) < 16:
                messages.error(request, "Numéro de carte invalide.")
                return redirect('ecommerce:checkout')
            if not card_expiry or len(card_expiry) != 5 or card_expiry[2] != '/':
                messages.error(request, "Date d'expiration invalide (format: MM/AA).")
                return redirect('ecommerce:checkout')
            if not card_cvv.isdigit() or len(card_cvv) < 3:
                messages.error(request, "CVV invalide.")
                return redirect('ecommerce:checkout')

        if payment_method in ['orange_money', 'mtn_money']:
            if not phone_number:
                messages.error(request, "Veuillez entrer un numéro de téléphone pour le paiement mobile.")
                return redirect('ecommerce:checkout')
            if not phone_number.startswith('+') or len(phone_number.replace(' ', '')) < 10:
                messages.error(request, "Numéro de téléphone invalide (ex: +225 01 23 45 67 89).")
                return redirect('ecommerce:checkout')

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_price=total_price,
                delivery_cost=delivery_cost,
                payment_method=payment_method,
                status='pending',
                card_number=card_number,
                card_expiry=card_expiry,
                card_cvv=card_cvv,
                card_holder=card_holder,
                phone_number=phone_number,
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.discounted_price
                )
                item.product.stock -= item.quantity
                item.product.save()

            # Envoyer l'email de confirmation
            context = {
                'user': request.user,
                'order': order,
                'request': request,
            }
            html_content = render_to_string('ecommerce/emails/order_confirmation.html', context)
            send_mail(
                subject='Confirmation de votre commande',
                message='Merci pour votre commande ! Voici les détails.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                html_message=html_content,
                fail_silently=False,
            )

            # Créer une notification pour l'utilisateur
            notification = Notification.objects.create(
                user=request.user,
                notification_type='order_details',
                message=f"Les détails de votre commande #{order.id} ont été envoyés à votre email.",
                action_url=reverse('orders:order_detail', args=[order.id])
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notifications_{request.user.id}',
                {
                    'type': 'send_notification',
                    'notification': {
                        'id': notification.id,
                        'notification_type': notification.notification_type,
                        'message': notification.message,
                        'created_at': notification.created_at.strftime('%d %b %Y %H:%M'),
                        'is_read': notification.is_read,
                        'action_url': notification.action_url
                    }
                }
            )

            # Créer des notifications pour les managers
            managers = CustomUser.objects.filter(is_manager=True)
            for manager in managers:
                notification = Notification.objects.create(
                    user=manager,
                    notification_type='new_order',
                    message=f"Nouvelle commande #{order.id} passée par {request.user.username}.",
                    action_url=reverse('users:manage_orders')
                )
                async_to_sync(channel_layer.group_send)(
                    f'notifications_{manager.id}',
                    {
                        'type': 'send_notification',
                        'notification': {
                            'id': notification.id,
                            'notification_type': notification.notification_type,
                            'message': notification.message,
                            'created_at': notification.created_at.strftime('%d %b %Y %H:%M'),
                            'is_read': notification.is_read,
                            'action_url': notification.action_url
                        }
                    }
                )

            cart.items.all().delete()
            messages.success(request, "Commande passée avec succès ! Un email de confirmation vous a été envoyé.")
            return redirect('orders:order_confirmation', order_id=order.id)

    return render(request, 'orders/checkout.html', {
        'cart': type('Cart', (), {'items': cart_items, 'total_amount': subtotal})(),
        'subtotal': subtotal,
        'delivery_cost': delivery_cost,
        'total_price': total_price,
        'addresses': addresses,
    })

@login_required(login_url='users:login')
def order_history(request):
    orders = Order.objects.filter(user=request.user).select_related('address').prefetch_related('items__product').order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})

@login_required(login_url='users:login')
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related('address').prefetch_related('items__product'), id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required(login_url='users:login')
def order_confirmation(request, order_id):
    order = get_object_or_404(Order.objects.select_related('address').prefetch_related('items__product'), id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})

@login_required(login_url='users:login')
def simulate_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    status_sequence = ['pending', 'processing', 'shipped', 'delivered']

    for status in status_sequence:
        order.status = status
        order.save()
        messages.success(request, f"Statut mis à jour : {status}")
        time.sleep(5)  # À remplacer par Celery en production

    return redirect('orders:order_detail', order_id=order.id)