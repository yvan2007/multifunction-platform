### multifunction_platform/context_processors.py
from ecommerce.models import Cart, CartItem, Product

def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = sum(item.quantity for item in cart.items.all())
        except Cart.DoesNotExist:
            count = 0
    else:
        if 'cart' in request.session:
            count = sum(request.session['cart'].values())
        else:
            count = 0
    return {'cart_item_count': count}