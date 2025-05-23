# Generated by Django 5.1.2 on 2024-12-08 14:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0001_initial"),
        ("leads", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="leads.userprofile",
            ),
        ),
    ]
