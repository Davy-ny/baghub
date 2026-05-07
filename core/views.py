from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import User
from orders.models import Order
from products.models import Product

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_dashboard(request):
    # Recent paid orders
    recent_orders = Order.objects.filter(status='paid').order_by('-created_at')[:10]
    # Low stock products (stock <= 2)
    low_stock_products = Product.objects.filter(stock__lte=2, stock__gt=0)
    out_of_stock = Product.objects.filter(stock=0)
    context = {
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
    }
    return render(request, 'core/admin_dashboard.html', context)
