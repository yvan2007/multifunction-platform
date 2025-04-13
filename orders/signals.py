# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Order
from users.models import Notification

@receiver(post_save, sender=Order)
def send_order_status_notification(sender, instance, created, **kwargs):
    if not created:  # Ne s'exécute pas lors de la création, seulement lors des mises à jour
        # Déterminer le statut de la commande
        status_messages = {
            'pending': 'En attente',
            'processing': 'En cours de traitement',
            'shipped': 'Expédiée',
            'delivered': 'Livrée',
            'cancelled': 'Annulée',
        }
        status_display = status_messages.get(instance.status, instance.status)

        # Sujet et message de l'e-mail
        subject = f"Mise à jour de votre commande #{instance.id}"
        message = (
            f"Bonjour,\n\n"
            f"Nous vous informons que votre commande #{instance.id} a été mise à jour.\n"
            f"Nouveau statut : {status_display}\n\n"
            f"Vous pouvez suivre l'évolution de votre commande ici : "
            f"http://127.0.0.1:8000/orders/order/{instance.id}/\n\n"
            f"Merci pour votre confiance !\n"
            f"Équipe [Votre Boutique]"
        )

        # Envoyer l'e-mail
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],  # Assurez-vous que `user` est lié à `Order` et a un champ `email`
            fail_silently=False,
        )



@receiver(post_save, sender=Order)
def order_notification(sender, instance, created, **kwargs):
    if created:
        # Nouvelle commande : notifier le client
        Notification.objects.create(
            user=instance.user,
            message=f"Votre commande #{instance.id} a été passée avec succès.",
            notification_type='new_order',
            action_url=reverse('orders:order_detail', args=[instance.id])
        )
        # Envoyer un email au client
        send_mail(
            subject=f"Nouvelle commande #{instance.id}",
            message=f"Votre commande a été passée avec succès.\n\nDétails: {instance}\n\nConsultez les détails: {instance.get_absolute_url()}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
            fail_silently=True,
        )
    elif instance.status == 'delivered':
        # Commande livrée : notifier le client
        Notification.objects.create(
            user=instance.user,
            message=f"Votre commande #{instance.id} a été livrée.",
            notification_type='order_delivered',
            action_url=reverse('orders:order_detail', args=[instance.id])
        )
        # Envoyer un email au client
        send_mail(
            subject=f"Commande #{instance.id} livrée",
            message=f"Votre commande a été livrée avec succès.\n\nDétails: {instance}\n\nConsultez les détails: {instance.get_absolute_url()}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
            fail_silently=True,
        )