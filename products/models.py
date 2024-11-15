from django.db import models

# from leads.models import Lead
# from clients.models import Client


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    leads = models.ManyToManyField("leads.Lead", related_name="products", blank=True)
    clients = models.ManyToManyField(
        "clients.Client", related_name="products", blank=True
    )

    def __str__(self):
        return self.name
