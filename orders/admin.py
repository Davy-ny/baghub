from django.contrib import admin
from .models import Order, OrderItem, Payment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total_amount', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'id')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'verified', 'mpesa_receipt', 'paid_at')
    list_filter = ('verified', 'paid_at')
    readonly_fields = ('paid_at',)

admin.site.register(Order, OrderAdmin)
admin.site.register(Payment, PaymentAdmin)