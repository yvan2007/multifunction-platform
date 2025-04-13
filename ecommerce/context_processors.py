from ecommerce.models import Cart, CartItem

def cart_count(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return {'cart_count': cart.items.count()}
    return {'cart_count': 0}