# Generated by Django 5.1.2 on 2025-01-02 18:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_order_payment_date_order_payment_status_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="order",
            name="payment_date",
        ),
        migrations.RemoveField(
            model_name="order",
            name="payment_status",
        ),
        migrations.RemoveField(
            model_name="order",
            name="stripe_session_id",
        ),
    ]
