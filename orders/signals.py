# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Order

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