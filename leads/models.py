from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from clients.models import Client
from django.db.models.signals import post_migrate
from django.apps import apps


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

    def get_lead_conversion_count(self):
        """
        Calculate the number of leads converted by the agent, grouped by category:
        "sale", "no sale".
        Exclude "new" category leads from the count.
        """
        leads = Lead.objects.filter(agent=self)
        lead_conversion_stats = {
            "sale": leads.filter(category__name="sale", is_converted=True).count(),
            "no_sale": leads.filter(
                category__name="no sale", is_converted=True
            ).count(),
        }

        # Calculate the conversion ratio for each category
        total_converted = sum(lead_conversion_stats.values())
        if total_converted > 0:
            lead_conversion_stats["sale_ratio"] = (
                lead_conversion_stats["sale"] / total_converted
            )
            lead_conversion_stats["no_sale_ratio"] = (
                lead_conversion_stats["no_sale"] / total_converted
            )
        else:
            lead_conversion_stats["sale_ratio"] = 0
            lead_conversion_stats["no_sale_ratio"] = 0

        return lead_conversion_stats

    def get_stats(self, start_date=None, end_date=None):
        """
        Aggregate all stats for the agent, including order stats and lead conversion stats.
        Allows for optional date range filtering for order stats.
        """
        order_stats = self.get_order_stats(start_date, end_date)
        lead_conversion_stats = self.get_lead_conversion_count()

        return {
            **order_stats,
            **lead_conversion_stats,
        }


class Lead(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    age = models.IntegerField(default=0)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=9, blank=True, null=True)
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
def create_client_from_lead(sender, instance, created, **kwargs):
    # Only trigger if the lead has been converted and it's not a newly created lead
    if not created and instance.is_converted and instance.category.name == "sale":
        # Check if a client with the same email already exists
        client, created = Client.objects.get_or_create(
            email=instance.email,  # Check if client with the same email exists
            defaults={  # This will only be used if the client doesn't exist
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "age": instance.age,
                "phone_number": instance.phone_number,
            },
        )

        # If a new client was created, log it or take any other necessary actions
        if created:
            print(
                f"A new client was created for {instance.first_name} {instance.last_name} ({instance.email})."
            )

        # If you want to handle an existing client case, you can do so here
        else:
            print(f"Client with email {instance.email} already exists.")


def create_default_categories(sender, **kwargs):
    """Create global categories."""
    Category = apps.get_model("leads", "Category")
    default_categories = ["new", "sale", "no sale"]
    for category_name in default_categories:
        Category.objects.get_or_create(name=category_name)


post_migrate.connect(create_default_categories)
