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
        # Create order (status='pending')
        order = Order.objects.create(user=request.user, total_amount=0, status='pending')
        total = 0
        for pid, qty in cart.items():
            product = Product.objects.get(id=int(pid))
            OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price)
            total += product.price * qty
            # ✅ Do NOT deduct stock here
        order.total_amount = total
        order.save()
        clear_cart(request)
        
        # Initiate M-Pesa payment
        return redirect('payment:initiate_mpesa', order_id=order.id)
    
    # GET request - show checkout confirmation
    cart_items = []
    total = 0
    for pid, qty in cart.items():
        product = Product.objects.get(id=int(pid))
        subtotal = product.price * qty
        total += subtotal
        cart_items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return render(request, 'orders/checkout.html', {'cart_items': cart_items, 'total': total})
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