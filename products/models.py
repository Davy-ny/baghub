from django.db import models
from django.conf import settings

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/')
    stock = models.PositiveIntegerField(default=1)
    available = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def reduce_stock(self, quantity):
        """Reduce stock by given quantity. Raises ValueError if insufficient stock."""
        if self.stock >= quantity:
            self.stock -= quantity
            if self.stock == 0:
                self.available = False
            self.save()
        else:
            raise ValueError(f"Insufficient stock for {self.name}. Available: {self.stock}, requested: {quantity}")
    
    # (Optional) if you already had mark_as_sold, you can keep it or remove it
    def mark_as_sold(self):
        """Convenience method to reduce stock by 1."""
        self.reduce_stock(1)
