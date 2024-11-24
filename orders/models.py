from django.db import models
from django.db.models import Sum, F
from clients.models import Client
from products.models import Product


class OrderManager(models.Manager):
    def total_revenue(self, start_date=None, end_date=None):
        """Calculate total revenue, optionally filtered by date range."""
        queryset = self.all()
        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        return (
            queryset.aggregate(
                total=Sum(
                    F("order_products__product_price") * F("order_products__quantity")
                )
            )["total"]
            or 0
        )

    def total_products_sold(self, start_date=None, end_date=None):
        """Calculate total quantity of products sold, optionally filtered by date range."""
        queryset = self.all()
        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        return queryset.aggregate(total=Sum("order_products__quantity"))["total"] or 0

    def order_statistics(self):
        """Calculate overall statistics for orders."""
        return {
            "total_revenue": self.total_revenue(),
            "total_products_sold": self.total_products_sold(),
            "total_orders": self.count(),
        }


class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders")
    date_created = models.DateTimeField(auto_now_add=True)
    objects = OrderManager()

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
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
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

    @classmethod
    def get_product_sales(cls, start_date=None, end_date=None):
        """Get the total quantity of each product sold."""
        queryset = cls.objects.all()

        # Apply date filters if provided
        if start_date:
            queryset = queryset.filter(order__date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(order__date_created__lte=end_date)

        # Aggregate total quantity sold per product, and include product info using select_related
        return (
            queryset.values("product_name")
            .annotate(total_quantity_sold=models.Sum("quantity"))
            .order_by("-total_quantity_sold")
        )

    def __str__(self):
        return f"{self.product_name} (x{self.quantity}) in Order {self.order.id}"
