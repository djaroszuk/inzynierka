from django.db import models
from django.db.models.signals import post_save, post_migrate
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.utils.timezone import now, timedelta
from django.apps import apps


# Custom User model with roles
class User(AbstractUser):
    is_organisor = models.BooleanField(default=True)
    is_agent = models.BooleanField(default=False)


# UserProfile model for one-to-one relation with User
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


# Agent model linked to User, with custom order stats methods
class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email

    def get_order_stats(self, start_date=None, end_date=None):
        # Calculate order stats (count, total value, average) for the agent
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
        # Get daily order data for the last `days` days
        today = now().date()
        start_date = today - timedelta(days=days - 1)

        daily_orders = (
            self.orders.filter(
                status="Paid", date_created__date__range=[start_date, today]
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
        # Get monthly revenue data for the last `months` months
        today = now().date()
        start_month = today.replace(day=1) - timedelta(days=30 * (months - 1))

        monthly_orders = (
            self.orders.filter(status="Paid", date_created__date__gte=start_month)
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
        # Calculate lead conversion count for the agent within the date range
        leads = Lead.objects.filter(agent=self, is_converted=True)

        if start_date:
            leads = leads.filter(conversion_date__gte=start_date)
        if end_date:
            leads = leads.filter(conversion_date__lte=end_date)

        sale_count = leads.filter(category__name__iexact="sale").count()
        no_sale_count = leads.filter(category__name__iexact="no sale").count()

        return {
            "sale": sale_count,
            "no_sale": no_sale_count,
        }

    def get_stats(self, start_date=None, end_date=None):
        # Aggregate order stats and lead conversion stats for the agent
        order_stats = self.get_order_stats(start_date, end_date)
        lead_conversion_stats = self.get_lead_conversion_count(start_date, end_date)

        return {
            **order_stats,
            **lead_conversion_stats,
        }


# Lead model for potential clients
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
        # Assign lead to a specific agent
        if self.agent is not None:
            raise ValueError("Lead is already assigned to an agent.")
        self.agent = agent
        self.save()

    def save(self, *args, **kwargs):
        # Detect change in `is_converted` state
        if self.pk:  # Instance exists
            previous = Lead.objects.get(pk=self.pk)
            self._is_converted_changed = not previous.is_converted and self.is_converted
        else:
            self._is_converted_changed = False  # New instance, no state change possible

        super().save(*args, **kwargs)


# Category model for categorizing leads
class Category(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


# Signal to create user profile on user creation
@receiver(post_save, sender=User)
def post_user_created_signal(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        if instance.is_organisor:
            instance.is_staff = True  # Grant admin access
            instance.is_superuser = True
            instance.save()


# Signal to create default categories after migrations
def create_default_categories(sender, **kwargs):
    Category = apps.get_model("leads", "Category")
    default_categories = ["new", "sale", "no sale"]
    for category_name in default_categories:
        Category.objects.get_or_create(name=category_name)


# Connect the post_migrate signal to create default categories
post_migrate.connect(create_default_categories)
