from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('initiate/<int:order_id>/', views.initiate_mpesa_payment_with_phone, name='initiate_mpesa'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    path('status/<int:order_id>/', views.payment_status, name='payment_status'),
    path('success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('initiate/<int:order_id>/<str:phone>/', views.initiate_mpesa_payment_with_phone, name='initiate_mpesa_with_phone'),
]