from celery import shared_task
from django.core.management import call_command


@shared_task
def cancel_expired_orders():
    """
    Call the custom management command to cancel expired orders.
    """
    call_command("cancel_expired_orders")  # Replace with the name of your command file
