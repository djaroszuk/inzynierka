from django.db import models
from clients.models import Client
from datetime import datetime


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    clients = models.ManyToManyField(Client, related_name="products", blank=True)

    def save(self, *args, **kwargs):
        if self.pk:  # If the product already exists
            old_product = Product.objects.get(pk=self.pk)
            if old_product.price != self.price:  # Check if the price has changed
                PriceHistory.objects.create(
                    product=self,
                    old_price=old_product.price,
                    new_price=self.price,
                    changed_at=datetime.now(),
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product, related_name="price_history", on_delete=models.CASCADE
    )
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)

    @property
    def price_delta(self):
        return self.new_price - self.old_price

    @property
    def absolute_delta(self):
        return abs(self.price_delta)

    def __str__(self):
        return f"{self.product.name}: {self.old_price} -> {self.new_price} at {self.changed_at}"
