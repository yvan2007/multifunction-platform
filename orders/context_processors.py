# orders/context_processors.py
from .models import Cart, CartItem
from ecommerce.models import Product

def cart_count(request):
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            # Only count CartItem objects with a valid Product
            cart_items = cart.items.all()
            for item in cart_items:
                try:
                    # Check if the product exists
                    Product.objects.get(id=item.product.id)
                    cart_count += 1
                except Product.DoesNotExist:
                    # Skip items with invalid products
                    continue
        except Cart.DoesNotExist:
            cart_count = 0
    else:
        # For unauthenticated users, count items in the session-based cart
        if 'cart' in request.session:
            cart = request.session['cart']
            # Only count items with a valid Product
            for product_id in cart.keys():
                try:
                    Product.objects.get(id=int(product_id))
                    cart_count += 1
                except Product.DoesNotExist:
                    continue
        else:
            cart_count = 0
    return {'cart_count': cart_count}