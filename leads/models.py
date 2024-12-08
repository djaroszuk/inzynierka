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

    def get_order_stats(self):
        """
        Calculate order stats for the agent.
        """
        orders = self.orders.all()
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
        Calculate the number of leads converted by the agent.
        """
        return Lead.objects.filter(agent=self, is_converted=True).count()

    def get_stats(self):
        """
        Aggregate all stats for the agent.
        """
        order_stats = self.get_order_stats()
        lead_conversion_count = self.get_lead_conversion_count()
        return {
            **order_stats,
            "lead_conversion_count": lead_conversion_count,
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
    if not created and instance.is_converted and not instance.client:
        # Create a new Client
        client = Client.objects.create(
            first_name=instance.first_name,
            last_name=instance.last_name,
            age=instance.age,
            email=instance.email,
            phone_number=instance.phone_number,
            organisation=instance.organisation,
            agent=instance.agent,
        )
        instance.client = client
        instance.save()


def create_default_categories(sender, **kwargs):
    """Create global categories."""
    Category = apps.get_model("leads", "Category")
    default_categories = ["new", "sale", "no sale"]
    for category_name in default_categories:
        Category.objects.get_or_create(name=category_name)


post_migrate.connect(create_default_categories)
