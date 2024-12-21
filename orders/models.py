from django.db import models
from django.db.models import Sum, F
from clients.models import Client
from products.models import Product
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.utils import timezone
from decimal import Decimal


class OrderManager(models.Manager):

    def total_revenue(self, start_date=None, end_date=None):
        """Calculate total revenue, optionally filtered by date range and order status (Accepted)."""
        queryset = self.filter(status="Accepted")  # Only consider accepted orders
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
        """Calculate total quantity of products sold, optionally filtered by date range and order status (Accepted)."""
        queryset = self.filter(status="Accepted")  # Only consider accepted orders
        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        return queryset.aggregate(total=Sum("order_products__quantity"))["total"] or 0

    def order_statistics(self):
        """Calculate overall statistics for orders, considering only accepted orders."""
        return {
            "total_revenue": self.total_revenue(),
            "total_products_sold": self.total_products_sold(),
            "total_orders": self.filter(status="Accepted").count(),
        }

    def orders_by_day(self):
        """Get the total orders grouped by day."""
        orders = (
            self.filter(status="Accepted")
            .annotate(day=TruncDay("date_created"))
            .values("day")
            .annotate(total_orders=Count("id"))
            .order_by("day")
        )
        return {
            "labels": [order["day"].strftime("%Y-%m-%d") for order in orders],
            "data": [order["total_orders"] for order in orders],
        }


class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders")
    date_created = models.DateTimeField(default=timezone.now)
    agent = models.ForeignKey(
        "leads.Agent",
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
    )  # Add this
    offer_token = models.CharField(max_length=255, blank=True, null=True, unique=True)
    objects = OrderManager()
    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Accepted", "Accepted"),
            ("Canceled", "Canceled"),
        ],
        default="Pending",
    )
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, help_text="Discount percentage"
    )

    @property
    def total_price(self):
        """
        Calculate the total price of all products in this order,
        including the discount if applicable.
        """
        return sum(
            item.product_price * item.quantity for item in self.order_products.all()
        )

    def __str__(self):
        return f"Order {self.id} for {self.client}"


class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_products"
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=100)  # Snapshot of product name
    product_price = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Snapshot price
    quantity = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        """Snapshot product name and price when saving."""
        if not self.product_name and self.product:
            self.product_name = self.product.name
        if not self.product_price and self.product:
            # Apply discount to product price
            discount_factor = Decimal("1.00") - (
                Decimal(self.order.discount) / Decimal(100)
            )
            self.product_price = self.product.price * discount_factor
        super().save(*args, **kwargs)

    def total_price(self):
        """Calculate the total price for this line in the order."""
        return self.product_price * self.quantity

    @classmethod
    def get_product_sales(cls, start_date=None, end_date=None):
        """
        Get the total quantity and total revenue of each product sold.
        Optionally filter by date range.
        """
        queryset = cls.objects.filter(order__status="Accepted")

        # Apply date filters if provided
        if start_date:
            queryset = queryset.filter(order__date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(order__date_created__lte=end_date)

        # Aggregate total quantity and total revenue sold per product
        return (
            queryset.values("product_name")
            .annotate(
                total_quantity_sold=Sum("quantity"),
                total_revenue_sold=Sum(F("quantity") * F("product_price")),
            )
            .order_by("-total_quantity_sold")
        )

    def __str__(self):
        return f"{self.product_name} (x{self.quantity}) in Order {self.order.id}"
