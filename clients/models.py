# clients/models.py
import random
from django.db import models


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
