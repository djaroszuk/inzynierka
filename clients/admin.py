from django.contrib import admin
from .models import Client, Contact


# ClientAdmin
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "status",
        "converted_date",
        "client_number",
    )
    list_filter = ("status", "converted_date")
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "client_number",
    )
    ordering = ("-converted_date",)
    readonly_fields = ("client_number",)

    def total_revenue(self, obj):
        return obj.total_revenue()

    total_revenue.short_description = "Total Revenue"

    def total_products_sold(self, obj):
        return obj.total_products_sold()

    total_products_sold.short_description = "Total Products Sold"


# ContactAdmin
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "reason",
        "description",
        "contact_date",
        "user",
    )
    list_filter = ("reason", "contact_date")
    search_fields = (
        "client__first_name",
        "client__last_name",
        "reason",
        "user__user__username",
    )
    ordering = ("-contact_date",)
