# clients/models.py
from django.db import models
from leads.models import Lead  # Import modelu Lead z aplikacji `leads`
from users.models import UserProfile  # Import UserProfile z aplikacji `users`


class Client(models.Model):
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, related_name="client")
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    age = models.IntegerField()
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    agent = models.ForeignKey(
        "leads.Agent", null=True, blank=True, on_delete=models.SET_NULL
    )  # Agent z aplikacji `leads`
    converted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - Client"
