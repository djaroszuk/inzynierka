from django.contrib import admin
from .models import Order, OrderProduct


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "date_created", "status", "total_price")
    list_filter = ("status", "date_created")
    search_fields = ("client__name", "client__email", "id")
    readonly_fields = ("status_history", "total_price")
    ordering = ("-date_created",)

    def total_price(self, obj):
        return obj.total_price

    total_price.short_description = "Total Price"


@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_name",
        "quantity",
        "product_price",
        "total_price",
    )
    list_filter = ("order__status", "product_name")
    search_fields = ("product_name", "order__id")
    readonly_fields = ("total_price",)

    def total_price(self, obj):
        return obj.total_price()

    total_price.short_description = "Total Price"
