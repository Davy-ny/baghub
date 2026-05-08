from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import json
from core.cart import get_cart, add_to_cart, remove_from_cart, clear_cart
from products.models import Product
from .models import Order, OrderItem

@csrf_exempt
def cart_add(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        add_to_cart(request, product_id)
        return JsonResponse({'message': 'Added to cart'}, status=200)

def cart_view(request):
    cart = get_cart(request)
    cart_items = []
    total = 0
    for pid, qty in cart.items():
        product = Product.objects.get(id=int(pid))
        subtotal = product.price * qty
        total += subtotal
        cart_items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return render(request, 'orders/cart.html', {'cart_items': cart_items, 'total': total})

def cart_remove(request, product_id):
    # Remove item from cart
    remove_from_cart(request, product_id)
    
    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'message': 'Item removed from cart'})
    
    # Otherwise redirect back to cart page
    return HttpResponseRedirect(reverse('orders:cart_view'))

@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart:
        return redirect('orders:cart_view')
    
    if request.method == 'POST':
        # Get phone number from form
        phone_number = request.POST.get('phone_number', '').strip()
        save_number = request.POST.get('save_number', False)
        
        # Validate phone number
        if not phone_number:
            messages.error(request, 'Phone number is required for M-Pesa payment.')
            # Re-render checkout with existing cart data
            cart_items, total = _get_cart_items_and_total(cart)
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items,
                'total': total,
                'phone_number': phone_number,
            })
        
        # Basic format: starts with 0 or +254 or 254, then 9 digits
        # Normalize to 254XXXXXXXXX format
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        elif not phone_number.startswith('254'):
            messages.error(request, 'Phone number must start with 0, 254, or +254')
            cart_items, total = _get_cart_items_and_total(cart)
            return render(request, 'orders/checkout.html', {'cart_items': cart_items, 'total': total})
        
        # Validate length (should be 12 digits after normalization)
        if len(phone_number) != 12 or not phone_number.isdigit():
            messages.error(request, 'Invalid phone number. Must be 12 digits (e.g., 2547XXXXXXXX)')
            cart_items, total = _get_cart_items_and_total(cart)
            return render(request, 'orders/checkout.html', {'cart_items': cart_items, 'total': total})
        
        # Save to user profile if requested
        if save_number:
            request.user.phone_number = phone_number
            request.user.save()
            messages.success(request, 'Phone number saved to your profile.')
        
        # Store phone number in session for payment initiation
        request.session['payment_phone'] = phone_number
        
        # Create order
        order = Order.objects.create(user=request.user, total_amount=0, status='pending')
        total = 0
        for pid, qty in cart.items():
            from products.models import Product
            product = Product.objects.get(id=int(pid))
            OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price)
            total += product.price * qty
        order.total_amount = total
        order.save()
        clear_cart(request)
        
        # Redirect to initiate payment with the provided phone number
        return redirect('payment:initiate_mpesa_with_phone', order_id=order.id, phone=phone_number)
    
    # GET request: show checkout form
    cart_items, total = _get_cart_items_and_total(cart)
    # Pre-fill with existing phone number if available
    initial_phone = request.user.phone_number or ''
    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'phone_number': initial_phone,
    })

def _get_cart_items_and_total(cart):
    from products.models import Product
    cart_items = []
    total = 0
    for pid, qty in cart.items():
        product = Product.objects.get(id=int(pid))
        subtotal = product.price * qty
        total += subtotal
        cart_items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return cart_items, total

from .models import Payment, Order
from django.urls import reverse

@login_required
def receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != 'paid':
        messages.warning(request, 'This order has not been paid yet.')
        return redirect('orders:cart_view')
    return render(request, 'orders/receipt.html', {'order': order})

@login_required
def confirm_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'paid':
        order.status = 'delivered'
        order.save()
        messages.success(request, 'Delivery confirmed. Thank you for shopping with BagHub!')
    else:
        messages.error(request, 'Only paid orders can be confirmed as delivered.')
    
    # Redirect to the order list page (or back to receipt if you prefer)
    return redirect('orders:order_list')

def payment_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'payments/payment_status.html', {'order': order})

@login_required
def order_list(request):
    """Display all orders for the logged-in customer."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})