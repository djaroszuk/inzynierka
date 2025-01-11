import random
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncMonth
from django.utils.timezone import now, timedelta


# Represents a client with personal details and related metrics
class Client(models.Model):
    class StatusChoices(models.TextChoices):
        REGULAR = "Regular", _("Regular")
        IMPORTANT = "Important", _("Important")

    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    age = models.IntegerField(blank=True, null=True)
    email = models.EmailField(
        unique=True, blank=True, null=True
    )  # Copy email from Lead
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    converted_date = models.DateTimeField(auto_now_add=True)
    client_number = models.CharField(max_length=20, unique=True, blank=True)

    # Client status
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.REGULAR,
    )

    def generate_client_number(self):
        # Generates a unique client number composed of digits.
        length = 8
        return "".join(random.choices("0123456789", k=length))

    def update_status(self):
        # Updates client status based on the number of paid orders.
        threshold = 2
        if self.orders.filter(status="Paid").count() > threshold:
            self.status = self.StatusChoices.IMPORTANT
        else:
            self.status = self.StatusChoices.REGULAR

    def save(self, *args, **kwargs):
        # Ensures a client number is assigned before saving.
        if not self.client_number:
            self.client_number = self.generate_client_number()
        super().save(*args, **kwargs)

    def total_revenue(self, start_date=None, end_date=None):
        # Calculates total revenue for the client.
        queryset = self.orders.filter(status="Paid")

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
        # Calculates total products sold for the client.
        queryset = self.orders.filter(status="Paid")

        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        return queryset.aggregate(total=Sum("order_products__quantity"))["total"] or 0

    def order_statistics(self, start_date=None, end_date=None):
        # Provides statistics on orders made by the client.
        queryset = self.orders.filter(status="Paid")

        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        return {
            "total_revenue": self.total_revenue(start_date, end_date),
            "total_products_sold": self.total_products_sold(start_date, end_date),
            "total_orders": queryset.count(),
        }

    def monthly_order_stats(self, start_date=None, end_date=None):
        # Calculates monthly order counts and spending totals.
        queryset = self.orders.filter(status="Paid")

        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        monthly_data = (
            queryset.annotate(month=TruncMonth("date_created"))
            .values("month")
            .annotate(
                order_count=Count("id"),
                total_spent=Sum(
                    F("order_products__product_price") * F("order_products__quantity")
                ),
            )
            .order_by("month")
        )

        return {
            "labels": [entry["month"].strftime("%Y-%m") for entry in monthly_data],
            "order_counts": [entry["order_count"] for entry in monthly_data],
            "total_spent": [entry["total_spent"] or 0 for entry in monthly_data],
        }

    def monthly_average_order_value(self, start_date=None, end_date=None):
        # Calculates monthly average order value (AOV).
        queryset = self.orders.filter(status="Paid")

        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        monthly_data = (
            queryset.annotate(month=TruncMonth("date_created"))
            .values("month")
            .annotate(
                order_count=Count("id"),
                total_spent=Sum(
                    F("order_products__product_price") * F("order_products__quantity")
                ),
            )
            .order_by("month")
        )

        return {
            "labels": [entry["month"].strftime("%Y-%m") for entry in monthly_data],
            "average_order_value": [
                (
                    round((entry["total_spent"] or 0) / entry["order_count"], 2)
                    if entry["order_count"] > 0
                    else 0
                )
                for entry in monthly_data
            ],
        }

    def lifetime_value_over_time(self):
        # Calculates lifetime value (LTV) for the client over the last year.
        end_date = now()
        start_date = end_date - timedelta(days=365)

        orders = self.orders.filter(
            status="Paid",
            date_created__gte=start_date,
            date_created__lte=end_date,
        )

        grouped_data = (
            orders.annotate(period=TruncMonth("date_created"))
            .values("period")
            .annotate(
                total_revenue=Sum(
                    F("order_products__product_price") * F("order_products__quantity")
                )
            )
            .order_by("period")
        )

        cumulative_revenue = 0
        ltv_data = {"labels": [], "ltv_values": []}
        for entry in grouped_data:
            cumulative_revenue += entry["total_revenue"] or 0
            ltv_data["labels"].append(entry["period"].strftime("%Y-%m"))
            ltv_data["ltv_values"].append(cumulative_revenue)

        return ltv_data

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# Represents a contact interaction with a client
class Contact(models.Model):
    class ReasonChoices(models.TextChoices):
        FOLLOW_UP = "Follow-up", _("Follow-up")
        SALES_OFFER = "Sales-offer", _("Sales-offer")
        SUPPORT = "Support", _("Support")
        COMPLAINT = "Complaint", _("Complaint")
        OTHER = "Other", _("Other")

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="contacts"
    )
    reason = models.CharField(max_length=20, choices=ReasonChoices.choices)
    description = models.TextField(blank=True, null=True)
    contact_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        "leads.UserProfile", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        user_name = self.user.user.username if self.user else "No User"
        return f"Contact with {self.client.first_name} ({self.reason}) by {user_name}"
