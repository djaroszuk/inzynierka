# clients/models.py
import random
from django.db import models
from django.utils.translation import gettext_lazy as _


class Client(models.Model):
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

    def generate_client_number(self):
        """Generuje unikalny numer klienta złożony tylko z cyfr."""
        length = 8  # długość numeru klienta
        return "".join(random.choices("0123456789", k=length))

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
    agent = models.ForeignKey(
        "leads.Agent", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"Contact with {self.client.first_name} ({self.reason}) by {self.agent.user.username}"
