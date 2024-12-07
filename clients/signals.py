from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order


@receiver(post_save, sender=Order)
def update_client_status_on_order_save(sender, instance, **kwargs):
    """
    Update the client's status to 'Important' if they meet the threshold
    for the number of accepted orders.
    """
    client = instance.client  # Get the client associated with the order
    if client:
        client.update_status()  # Call the update_status method
        client.save()  # Save the updated client object
