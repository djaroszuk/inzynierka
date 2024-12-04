from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from clients.models import Client


class User(AbstractUser):
    is_organisor = models.BooleanField(default=True)
    is_agent = models.BooleanField(default=False)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class Lead(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    age = models.IntegerField(default=0)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=9, blank=True, null=True)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
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
    client = models.OneToOneField(
        "clients.Client",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="lead",
    )

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


class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email


class Category(models.Model):
    name = models.CharField(max_length=30)
    organisation = models.ForeignKey("leads.UserProfile", on_delete=models.CASCADE)

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


@receiver(post_save, sender=UserProfile)
def create_default_categories(sender, instance, created, **kwargs):
    """Create default categories when a new organizer (UserProfile) is created."""
    if created and instance.user.is_organisor:
        # Default categories to create
        default_categories = ["new", "sale", "no sale"]

        # Create the categories for the associated UserProfile (team)
        for category_name in default_categories:
            # Only create the category if it doesn't already exist for this team
            Category.objects.get_or_create(name=category_name, organisation=instance)
