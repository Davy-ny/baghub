CART_SESSION_KEY = 'cart'

def get_cart(request):
    return request.session.get(CART_SESSION_KEY, {})

def add_to_cart(request, product_id, quantity=1):
    cart = get_cart(request)
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    request.session[CART_SESSION_KEY] = cart

def remove_from_cart(request, product_id):
    cart = get_cart(request)
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session[CART_SESSION_KEY] = cart

def clear_cart(request):
    request.session[CART_SESSION_KEY] = {}