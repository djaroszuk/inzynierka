# Generated by Django 5.1.2 on 2024-12-15 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="conversion_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
