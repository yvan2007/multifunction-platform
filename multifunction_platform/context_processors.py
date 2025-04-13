# multifunction_platform/context_processors.py
from ecommerce.models import Cart, CartItem, Product

def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.items.count()  # Compte le nombre d'éléments distincts
        except Cart.DoesNotExist:
            count = 0
    else:
        if 'cart' in request.session:
            count = len(request.session['cart'])
        else:
            count = 0
    return {'cart_item_count': count}