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


# Category model for organizing notes
class NoteCategory(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# Preset Pattern model for notes
class NoteTemplate(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self):
        return self.title


class Note(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="notes")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="notes")
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        NoteCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
    )
    template = models.ForeignKey(
        NoteTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
    )

    def __str__(self):
        return f"Note by {self.agent.user.username} on {self.lead.first_name} {self.lead.last_name} at {self.date_created}"

    class Meta:
        ordering = ["-date_created"]  # Order notes by most recent first

    # def export_to_doc(self):
    #     """Export the note to a DOCX file.""" #TODO
    #     from docx import Document

    #     doc = Document()
    #     doc.add_heading(f"Note for {self.lead.first_name} {self.lead.last_name}", 0)
    #     doc.add_paragraph(f"Agent: {self.agent.user.username}")
    #     doc.add_paragraph(f"Date Created: {self.date_created}")
    #     doc.add_paragraph(f"Category: {self.category.name if self.category else 'No Category'}")
    #     doc.add_paragraph(f"Note Content: {self.content}")

    #     # Save the document to a file (you can adjust the filename or path as needed)
    #     filename = f"Note_{self.id}.docx"
    #     doc.save(f"/path/to/save/{filename}")

    #     return filename


def post_user_created_signal(sender, instance, created, **kwargs):
    print(instance)
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(post_user_created_signal, sender=User)


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
