# Generated by Django 5.1.2 on 2024-12-28 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0002_lead_conversion_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lead",
            name="age",
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name="lead",
            name="email",
            field=models.EmailField(
                default="example@example.com", max_length=254, unique=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="lead",
            name="phone_number",
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
