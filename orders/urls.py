from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/', views.cart_add, name='cart_add'),
     path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('receipt/<int:order_id>/', views.receipt, name='receipt'),
    path('my-orders/', views.order_list, name='order_list'),
    path('confirm-delivery/<int:order_id>/', views.confirm_delivery, name='confirm_delivery'),
    path('payment-status/<int:order_id>/', views.payment_status, name='payment_status'),
]