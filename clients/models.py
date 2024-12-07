# clients/models.py
import random
from django.db import models
from django.utils.translation import gettext_lazy as _


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

    # Powiązanie z organizacją i agentem z `leads`
    organisation = models.ForeignKey(
        "leads.UserProfile", null=True, blank=True, on_delete=models.CASCADE
    )
    agent = models.ForeignKey(
        "leads.Agent", null=True, blank=True, on_delete=models.SET_NULL
    )

    # Data konwersji leadu na klienta
    converted_date = models.DateTimeField(auto_now_add=True)

    # Automatycznie generowany numer klienta
    client_number = models.CharField(max_length=20, unique=True, blank=True)

    # Client status
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.REGULAR,
    )

    def generate_client_number(self):
        """Generuje unikalny numer klienta złożony tylko z cyfr."""
        length = 8  # długość numeru klienta
        return "".join(random.choices("0123456789", k=length))

    def update_status(self):
        """Updates client status to 'Important' if they exceed a threshold of orders."""
        threshold = 2  # Number of orders to qualify as 'Important'
        if self.orders.filter(status="Accepted").count() > threshold:
            self.status = self.StatusChoices.IMPORTANT
        else:
            self.status = self.StatusChoices.REGULAR

    def save(self, *args, **kwargs):
        """Przypisuje numer klienta przed zapisaniem obiektu, jeśli jeszcze nie istnieje."""
        if not self.client_number:
            self.client_number = self.generate_client_number()
        super().save(*args, **kwargs)

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
