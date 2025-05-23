# Standard Library Imports
from decimal import Decimal

# Django Core Imports
from django.db import models
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncDay
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import now

# Models
from clients.models import Client
from products.models import Product


# Manages order-related queries and statistics
class OrderManager(models.Manager):

    def total_revenue(self, start_date=None, end_date=None):
        # Calculates total revenue for paid orders within an optional date range
        queryset = self.filter(status="Paid")
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
        # Calculates total products sold for paid orders within an optional date range
        queryset = self.filter(status="Paid")
        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        return queryset.aggregate(total=Sum("order_products__quantity"))["total"] or 0

    def order_statistics(self):
        # Provides general statistics for all paid orders
        return {
            "total_revenue": self.total_revenue(),
            "total_products_sold": self.total_products_sold(),
            "total_orders": self.filter(status="Paid").count(),
        }

    def orders_by_day(self):
        # Groups and counts paid orders by the day they were created
        orders = (
            self.filter(status="Paid")
            .annotate(day=TruncDay("date_created"))
            .values("day")
            .annotate(total_orders=Count("id"))
            .order_by("day")
        )
        return {
            "labels": [order["day"].strftime("%Y-%m-%d") for order in orders],
            "data": [order["total_orders"] for order in orders],
        }


# Represents an individual order and its details
class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders")
    date_created = models.DateTimeField(default=timezone.now)
    agent = models.ForeignKey(
        "leads.Agent",
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
    )
    offer_token = models.CharField(max_length=255, blank=True, null=True, unique=True)
    objects = OrderManager()
    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Accepted", "Accepted"),
            ("Canceled", "Canceled"),
            ("Paid", "Paid"),
        ],
        default="Pending",
    )
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, help_text="Discount percentage"
    )

    DISCOUNT_CHOICES = {
        "0": Decimal("0.00"),
        "5": Decimal("0.05"),
        "10": Decimal("0.10"),
        "15": Decimal("0.15"),
    }
    status_history = models.JSONField(default=list, blank=True)

    @property
    def total_price(self):
        # Calculates the total price of the order, accounting for product quantities
        return sum(
            item.product_price * item.quantity for item in self.order_products.all()
        )

    def get_discount_percentage(self):
        # Provides discount choices formatted for display
        return [
            (key, f"{value * 100:.0f}%") for key, value in self.DISCOUNT_CHOICES.items()
        ]

    def save(self, *args, **kwargs):
        # Overrides save to log status changes
        if self.pk:
            old_status = Order.objects.get(pk=self.pk).status
            if old_status != self.status:
                self.status_history.append(
                    {
                        "previous_status": old_status,
                        "new_status": self.status,
                        "changed_at": now().isoformat(),
                    }
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} for {self.client}"


# Represents a product within an order
class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_products"
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=100)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        # Saves product snapshots (name and price) when creating or updating
        if not self.product_name and self.product:
            self.product_name = self.product.name
        if not self.product_price and self.product:
            discount_factor = Decimal("1.00") - (
                Decimal(self.order.discount) / Decimal(100)
            )
            self.product_price = self.product.price * discount_factor
        super().save(*args, **kwargs)

    def total_price(self):
        # Calculates the total price for this product line
        return self.product_price * self.quantity

    @classmethod
    def get_product_sales(cls, start_date=None, end_date=None):
        # Retrieves sales data for products, optionally filtered by date range
        queryset = cls.objects.filter(order__status="Paid")

        if start_date:
            queryset = queryset.filter(order__date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(order__date_created__lte=end_date)

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


@receiver(post_save, sender=Order)
def update_client_status_on_order_save(sender, instance, **kwargs):
    # Updates client status based on order history when an order is saved
    client = instance.client
    if client:
        client.update_status()
        client.save()
