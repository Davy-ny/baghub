from django.contrib import admin
from .models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'available', 'created_by', 'created_at')
    list_filter = ('available', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock', 'available')
    readonly_fields = ('created_at',)

admin.site.register(Product, ProductAdmin)