# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from ecommerce.models import Product
from django.conf import settings
from django.contrib.auth.models import User

class CustomUser(AbstractUser):
    is_manager = models.BooleanField(default=False)
    secret_code = models.CharField(max_length=10, blank=True, null=True)

    def generate_secret_code(self):
        import random
        import string
        self.secret_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.save()

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Remplacer User par settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Remplacer User par settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.postal_code}, {self.country}"

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites'  # Cette relation inverse permet d'utiliser request.user.favorites
    )
    product = models.ForeignKey(
        'ecommerce.Product',  # Assumes that the Product model is in the ecommerce app
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Un utilisateur ne peut ajouter un produit qu'une seule fois dans ses favoris

    def __str__(self):
        return f"{self.user.username} favors {self.product.name}"

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Vérifier que le message est entre un client et un gestionnaire
        if self.sender.is_manager and not self.recipient.is_manager:
            pass  # Gestionnaire -> Client : OK
        elif not self.sender.is_manager and self.recipient.is_manager:
            pass  # Client -> Gestionnaire : OK
        else:
            raise ValueError("Les messages ne peuvent être envoyés qu'entre clients et gestionnaires.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"De {self.sender} à {self.recipient} - {self.subject}"

# users/models.py
class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('new_message', 'Nouveau message'),
            ('new_order', 'Nouvelle commande'),
            ('order_details', 'Détails de la commande'),
            ('order_delivered', 'Commande livrée'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    action_url = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.message} pour {self.user.username}"
    
class PaymentMethod(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Remplacer User par settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    card_type = models.CharField(max_length=50)  # Ex: "Visa", "MasterCard"
    last_four_digits = models.CharField(max_length=4)
    expiry_date = models.DateField()
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.card_type} ending in {self.last_four_digits}"