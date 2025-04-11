from django.db import models
from django.conf import settings

class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_amount(self):
        """Calculate the total amount of the cart."""
        return sum(item.total_price for item in self.items.all())

# Modèle pour les éléments du panier
class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        'ecommerce.Product',
        on_delete=models.CASCADE,
        related_name='ecommerce_cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart"

    @property
    def total_price(self):
        """Calculate the total price for this cart item (price * quantity)."""
        return self.product.price * self.quantity

# Modèle pour une commande
class Order(models.Model):
    PAYMENT_METHODS = (
        ('orange_money', 'Orange Money'),
        ('mtn_money', 'Wave'),  # Align with template's "Wave"
        ('card', 'Carte Bancaire'),  # Align with template's "Carte Bancaire"
        ('cod', 'Paiement à la livraison'),
    )
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('processing', 'En traitement'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    address = models.ForeignKey(
        'users.Address',
        on_delete=models.SET_NULL,
        null=True
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='cod'
    )
    delivery_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Card details fields (for demonstration purposes only)
    card_number = models.CharField(max_length=20, blank=True, null=True)
    card_expiry = models.CharField(max_length=5, blank=True, null=True)  # Format: MM/AA
    card_cvv = models.CharField(max_length=4, blank=True, null=True)
    card_holder = models.CharField(max_length=100, blank=True, null=True)
    # Phone number for mobile payments
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    class Meta:
        ordering = ['-created_at']

# Modèle pour les éléments d'une commande
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        'ecommerce.Product',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )  # Price at the time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in order {self.order.id}"

    @property
    def total_price(self):
        """Calculate the total price for this order item (price * quantity)."""
        return self.price * self.quantity