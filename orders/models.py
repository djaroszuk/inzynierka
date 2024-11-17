# orders/models.py
from django.db import models
from clients.models import Client
from products.models import Product


class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders")
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} for {self.client}"


class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_products"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in Order {self.order.id}"
