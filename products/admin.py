from django.contrib import admin
from .models import Product, PriceHistory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock_quantity", "get_clients")
    list_filter = ("price",)
    search_fields = ("name", "description")
    ordering = ("name",)

    def get_clients(self, obj):
        return ", ".join([client.name for client in obj.clients.all()])

    get_clients.short_description = "Clients"


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("product", "old_price", "new_price", "changed_at", "absolute_delta")
    list_filter = ("changed_at",)
    search_fields = ("product__name",)
    ordering = ("-changed_at",)
