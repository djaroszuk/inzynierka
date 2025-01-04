from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from clients.models import Client, Contact
from django.db.models.signals import post_migrate
from django.apps import apps
from django.db.models.functions import TruncDay
from django.db.models import Count
from django.utils.timezone import now, timedelta
from django.utils import timezone


class User(AbstractUser):
    is_organisor = models.BooleanField(default=True)
    is_agent = models.BooleanField(default=False)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email

    def get_order_stats(self, start_date=None, end_date=None):
        """
        Calculate order stats for the agent, filtered by the given date range.
        """
        orders = self.orders.all()

        if start_date:
            orders = orders.filter(date_created__gte=start_date)
        if end_date:
            orders = orders.filter(date_created__lte=end_date)

        order_count = orders.count()
        total_value = sum(order.total_price for order in orders)
        average_order_value = total_value / order_count if order_count > 0 else 0

        return {
            "order_count": order_count,
            "total_value": total_value,
            "average_order_value": average_order_value,
        }

    def get_daily_order_data(self, days=7):
        """
        Return a list of dictionaries containing 'date' and 'count' of accepted orders
        for the last `days` days.
        Format: [{"date": "YYYY-MM-DD", "count": int}, ...]
        """
        today = now().date()
        start_date = today - timedelta(days=days - 1)

        daily_orders = (
            self.orders.filter(
                status="Accepted", date_created__date__range=[start_date, today]
            )
            .annotate(day=TruncDay("date_created"))
            .values("day")
            .annotate(order_count=Count("id"))
            .order_by("day")
        )

        daily_orders_data = [
            {"date": entry["day"].strftime("%Y-%m-%d"), "count": entry["order_count"]}
            for entry in daily_orders
        ]
        return daily_orders_data

    def get_monthly_revenue_data(self, months=6):
        """
        Return a list of dictionaries containing 'month' and 'revenue' of accepted orders
        for the last `months` months.
        Format: [{"month": "YYYY-MM", "revenue": float}, ...]
        """
        from django.db.models.functions import TruncMonth
        from django.db.models import Sum, F

        today = now().date()
        # Approximate start date by going ~months*30 days back or pick first day of current month - logic can vary
        # For simplicity, we just count last X months including partial months
        # Better approach: find first day of (today - X months)
        start_month = today.replace(day=1) - timedelta(days=30 * (months - 1))

        monthly_orders = (
            self.orders.filter(status="Accepted", date_created__date__gte=start_month)
            .annotate(month=TruncMonth("date_created"))
            .values("month")
            .annotate(
                monthly_revenue=Sum(
                    F("order_products__product_price") * F("order_products__quantity")
                )
            )
            .order_by("month")
        )

        monthly_revenue_data = [
            {
                "month": entry["month"].strftime("%Y-%m"),
                "revenue": float(entry["monthly_revenue"] or 0),
            }
            for entry in monthly_orders
        ]
        return monthly_revenue_data

    def get_lead_conversion_count(self, start_date=None, end_date=None):
        """
        Calculate the number of leads converted by the agent within the given date range,
        grouped by category: "sale", "no sale".
        Filters based on conversion_date instead of date_created.
        """
        leads = Lead.objects.filter(agent=self, is_converted=True)

        # Filter based on conversion_date
        if start_date:
            leads = leads.filter(conversion_date__gte=start_date)
        if end_date:
            leads = leads.filter(conversion_date__lte=end_date)

        # Filter out 'new' category leads
        sale_count = leads.filter(category__name__iexact="sale").count()
        no_sale_count = leads.filter(category__name__iexact="no sale").count()

        return {
            "sale": sale_count,
            "no_sale": no_sale_count,
        }

    def get_stats(self, start_date=None, end_date=None):
        """
        Aggregate all stats for the agent, including order stats and lead conversion stats.
        Allows for optional date range filtering for order stats.
        """
        order_stats = self.get_order_stats(start_date, end_date)
        lead_conversion_stats = self.get_lead_conversion_count(
            start_date, end_date
        )  # Add start_date, end_date here

        return {
            **order_stats,
            **lead_conversion_stats,
        }


class Lead(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    age = models.IntegerField(default=0, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    agent = models.ForeignKey("Agent", null=True, blank=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(
        "Category",
        related_name="leads",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    is_converted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    convert = models.BooleanField(default=False)
    conversion_date = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def assign_to_agent(self, agent):
        """
        Assign the lead to a specific agent.
        """
        if self.agent is not None:
            raise ValueError("Lead is already assigned to an agent.")
        self.agent = agent
        self.save()

    def save(self, *args, **kwargs):
        # Check for a state change in `is_converted`
        if self.pk:  # Instance exists
            previous = Lead.objects.get(pk=self.pk)
            self._is_converted_changed = not previous.is_converted and self.is_converted
        else:
            self._is_converted_changed = False  # New instance, no state change possible

        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


@receiver(post_save, sender=User)
def post_user_created_signal(sender, instance, created, **kwargs):
    if created:
        print(f"Signal triggered for user: {instance.username}")
        UserProfile.objects.create(user=instance)
        if instance.is_organisor:
            instance.is_staff = True  # Grant admin panel access
            instance.is_superuser = True
            instance.save()


@receiver(post_save, sender=Lead)
def handle_lead_conversion(sender, instance, created, **kwargs):
    """
    Handle actions after a Lead's `convert` field is set to True.
    - Triggers only when `convert` is True.
    """

    if instance.convert:  # Trigger only when `convert` is True
        print(f"Signal 'handle_lead_conversion' triggered for Lead: {instance}")

        # Mark the lead as converted
        instance.is_converted = True
        instance.convert = False  # Reset `convert` to prevent retriggering
        instance.save(update_fields=["is_converted", "convert"])

        # Set conversion date if not already set
        if not instance.conversion_date:
            instance.conversion_date = timezone.now()
            instance.save(update_fields=["conversion_date"])

        # Handle the conversion logic for category and client creation
        if instance.category and instance.category.name.lower() == "sale":
            # Check if a client with the same email already exists
            client, created_client = Client.objects.get_or_create(
                email=instance.email,
                defaults={
                    "first_name": instance.first_name,
                    "last_name": instance.last_name,
                    "age": instance.age,
                    "phone_number": instance.phone_number,
                },
            )

            if created_client:
                print(
                    f"A new client was created for {instance.first_name} {instance.last_name} ({instance.email})."
                )

                # Create a contact with category 'Other' with info about when the client was created
                Contact.objects.create(
                    client=client,
                    reason=Contact.ReasonChoices.OTHER,
                    description=(
                        f"Client created on {now().strftime('%Y-%m-%d %H:%M:%S')}. "
                        f"Lead comment: {instance.comment or 'No comment provided.'}"
                    ),
                )
            else:
                print(f"Client with email {instance.email} already exists.")


def create_default_categories(sender, **kwargs):
    """Create global categories."""
    Category = apps.get_model("leads", "Category")
    default_categories = ["new", "sale", "no sale"]
    for category_name in default_categories:
        Category.objects.get_or_create(name=category_name)


post_migrate.connect(create_default_categories)
