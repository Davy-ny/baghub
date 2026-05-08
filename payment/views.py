from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from baghub_project import settings
from baghub_project import settings
from orders.models import Order, Payment
from .mpesa import stk_push
import json

@login_required
def initiate_mpesa_payment_with_phone(request, order_id, phone):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != 'pending':
        messages.error(request, 'This order has already been processed.')
        return redirect('products:product_list')
    
    # Check stock again
    for item in order.items.all():
        if item.product.stock < item.quantity:
            messages.error(request, f"Sorry, {item.product.name} is now out of stock.")
            order.status = 'cancelled'
            order.save()
            return redirect('orders:cart_view')
    
    # Format phone number (already normalized in checkout)
    # But ensure it's in correct format 254XXXXXXXXX
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+'):
        phone = phone[1:]
    
    response = stk_push(
        phone_number=phone,
        amount=float(order.total_amount),
        account_reference=f'BagHubOrder{order.id}',
        transaction_desc='Bag purchase',
        order_id=order.id
    )
    
    if response.get('ResponseCode') == '0':
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'amount': order.total_amount,
            }
        )
        payment.mpesa_checkout_request_id = response.get('CheckoutRequestID')
        payment.amount = order.total_amount
        payment.save()
        messages.info(request, 'STK push sent. Please check your phone and enter PIN.')
        return redirect('payment:payment_status', order_id=order.id)
    else:
        messages.error(request, f"Payment initiation failed: {response.get('errorMessage', 'Unknown error')}")
        return redirect('orders:checkout')

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        callback_metadata = stk_callback.get('CallbackMetadata', {})
        
        try:
            payment = Payment.objects.get(mpesa_checkout_request_id=checkout_request_id)
        except Payment.DoesNotExist:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Payment not found'})
        
        order = payment.order
        
        if result_code == 0:
            # Payment success
            items = callback_metadata.get('Item', [])
            mpesa_receipt = next((item['Value'] for item in items if item['Name'] == 'MpesaReceiptNumber'), '')
            amount = next((item['Value'] for item in items if item['Name'] == 'Amount'), 0)
            
            # ✅ Deduct stock for each order item
            try:
                for order_item in order.items.all():
                    product = order_item.product
                    product.reduce_stock(order_item.quantity)  # you must define this method
                order.status = 'paid'
                order.save()
                payment.verified = True
                payment.mpesa_result_code = 0
                payment.mpesa_result_desc = 'Success'
                payment.mpesa_receipt = mpesa_receipt
                payment.save()
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
            except ValueError as e:
                # Not enough stock – cancel order and refund
                order.status = 'cancelled'
                order.save()
                return JsonResponse({'ResultCode': 1, 'ResultDesc': f'Stock error: {str(e)}'})
        else:
            # Payment failed – order remains pending, no stock change
            payment.mpesa_result_code = result_code
            payment.mpesa_result_desc = stk_callback.get('ResultDesc', 'Failed')
            payment.save()
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Payment failed'})
    
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid request'})

@login_required
def payment_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = getattr(order, 'payment', None)
    
    # If the order is already paid, redirect to success page
    if order.status == 'paid':
        return redirect('payment:payment_success', order_id=order.id)
    
    # Check if payment verification happened (callback already processed)
    if payment and payment.verified:
        # Refresh order status from database
        order.refresh_from_db()
        if order.status == 'paid':
            return redirect('payment:payment_success', order_id=order.id)
    
    return render(request, 'payments/payment_status.html', {'order': order, 'payment': payment})

@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != 'paid':
        # If not paid, redirect to payment status page
        return redirect('payment:payment_status', order_id=order.id)
    
    context = {
        'order': order,
        'vendor_name': settings.VENDOR_NAME,
        'vendor_email': settings.VENDOR_EMAIL,
        'vendor_phone': settings.VENDOR_PHONE,
        'vendor_address': settings.VENDOR_ADDRESS,
    }
    return render(request, 'payments/success.html', context)
