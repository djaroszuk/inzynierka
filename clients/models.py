import random
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
import datetime


class Client(models.Model):
    class StatusChoices(models.TextChoices):
        REGULAR = "Regular", _("Regular")
        IMPORTANT = "Important", _("Important")

    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    age = models.IntegerField()
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
        """Generates a unique client number composed of digits."""
        length = 8  # Length of the client number
        return "".join(random.choices("0123456789", k=length))

    def update_status(self):
        """Updates client status to 'Important' if they exceed a threshold of accepted orders."""
        threshold = 2  # Number of accepted orders to qualify as 'Important'
        if self.orders.filter(status="Accepted").count() > threshold:
            self.status = self.StatusChoices.IMPORTANT
        else:
            self.status = self.StatusChoices.REGULAR

    def save(self, *args, **kwargs):
        """Assigns a client number before saving if it doesn't already exist."""
        if not self.client_number:
            self.client_number = self.generate_client_number()
        super().save(*args, **kwargs)

    def total_revenue(self, start_date=None, end_date=None):
        """Calculate total revenue for this client, considering only accepted orders."""
        queryset = self.orders.filter(status="Accepted")

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
        """Calculate total products sold for this client, considering only accepted orders."""
        queryset = self.orders.filter(status="Accepted")

        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        return queryset.aggregate(total=Sum("order_products__quantity"))["total"] or 0

    def order_statistics(self, start_date=None, end_date=None):
        """Calculate order-related statistics for this client."""
        queryset = self.orders.filter(status="Accepted")

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
        """
        Calculate the monthly number of accepted orders and total amount spent.
        Returns a dictionary with 'labels', 'order_counts', and 'total_spent'.
        """
        queryset = self.orders.filter(status="Accepted")

        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_created__lte=end_date)

        # Annotate each order with the month it was created
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
        """
        Calculate the monthly Average Order Value (AOV) for the client.
        Returns a dictionary with 'labels' and 'average_order_value'.
        """
        # Handle the case where there are no orders
        if not self.orders.exists():
            return {
                "labels": [],
                "average_order_value": [],
            }

        if not start_date:
            # Get the earliest order's date_created and convert to date, set day=1
            start_order = self.orders.earliest("date_created")
            start_date = start_order.date_created.replace(day=1).date()
        else:
            # Ensure start_date is a date object
            if isinstance(start_date, datetime.datetime):
                start_date = start_date.date()

        if not end_date:
            end_date = timezone.now().date()
        else:
            # Ensure end_date is a date object
            if isinstance(end_date, datetime.datetime):
                end_date = end_date.date()

        # Generate all months between start_date and end_date
        months = []
        current = start_date.replace(day=1)
        while current <= end_date:
            months.append(current.strftime("%Y-%m"))
            # Move to the next month
            year = current.year + (current.month // 12)
            month = (current.month % 12) + 1
            try:
                current = current.replace(year=year, month=month, day=1)
            except ValueError:
                # Handle month rollover if needed
                current = datetime.date(year, month, 1)

        # Fetch existing monthly data
        queryset = self.orders.filter(
            status="Accepted", date_created__gte=start_date, date_created__lte=end_date
        )
        if not queryset.exists():
            # If no orders are found in the date range, return zeros for all months
            return {
                "labels": months,
                "average_order_value": [0.0] * len(months),
            }

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

        # Create a dictionary from the queryset for easy lookup
        data_dict = {entry["month"].strftime("%Y-%m"): entry for entry in monthly_data}

        # Prepare the final data, filling in zeros where necessary
        average_order_value = []
        for month in months:
            if month in data_dict and data_dict[month]["order_count"] > 0:
                aov = (
                    float(data_dict[month]["total_spent"])
                    / data_dict[month]["order_count"]
                )
                average_order_value.append(round(aov, 2))  # Rounded to 2 decimal places
            else:
                average_order_value.append(0.0)

        return {
            "labels": months,
            "average_order_value": average_order_value,
        }

    def lifetime_value_over_time(self, group_by="year"):
        """
        Calculate the customer's lifetime value grouped by the specified time period.
        group_by can be 'month', 'quarter', or 'year'.
        Returns a dictionary with grouped periods and cumulative revenue.
        """
        from django.db.models.functions import TruncMonth, TruncQuarter, TruncYear
        from django.db.models import Sum

        # Define the grouping logic
        if group_by == "month":
            group_by_trunc = TruncMonth("date_created")
        elif group_by == "quarter":
            group_by_trunc = TruncQuarter("date_created")
        elif group_by == "year":
            group_by_trunc = TruncYear("date_created")
        else:
            raise ValueError(
                "Invalid group_by value. Choose 'month', 'quarter', or 'year'."
            )

        # Aggregate revenue grouped by the chosen period
        orders = self.orders.filter(status="Accepted")
        grouped_data = (
            orders.annotate(period=group_by_trunc)
            .values("period")
            .annotate(
                total_revenue=Sum(
                    F("order_products__product_price") * F("order_products__quantity")
                )
            )
            .order_by("period")
        )

        # Calculate cumulative revenue
        cumulative_revenue = 0
        ltv_data = {"labels": [], "ltv_values": []}
        for entry in grouped_data:
            cumulative_revenue += entry["total_revenue"] or 0
            ltv_data["labels"].append(entry["period"].strftime("%Y-%m-%d"))
            ltv_data["ltv_values"].append(cumulative_revenue)

        return ltv_data

    def __str__(self):
        return f"{self.first_name} {self.last_name} - Client"


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
