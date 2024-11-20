from django.db import models
from clients.models import Client
from products.models import Product


class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders")
    date_created = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        """Calculate the total price of all products in this order."""
        return sum(item.total_price() for item in self.order_products.all())

    def __str__(self):
        return f"Order {self.id} for {self.client}"


class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_products"
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True
    )  # Use SET_NULL
    product_name = models.CharField(max_length=100)  # Save product name (snapshot)
    product_price = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Save product price (snapshot)
    quantity = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        """Snapshot product name and price when saving."""
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_price:
            self.product_price = self.product.price
        super().save(*args, **kwargs)

    def total_price(self):
        """Calculate the total price for this line in the order."""
        return self.product_price * self.quantity

    def __str__(self):
        return f"{self.product_name} (x{self.quantity}) in Order {self.order.id}"
