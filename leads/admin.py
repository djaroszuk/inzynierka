from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.contrib import messages

from .models import User, UserProfile, Agent, Lead, Category
from clients.models import Client  # Ensure this is correctly imported


# Custom UserAdmin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "is_organisor",
        "is_agent",
        "is_staff",
        "is_superuser",
    )
    list_filter = ("is_organisor", "is_agent", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {"fields": ("is_organisor", "is_agent")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {"fields": ("is_organisor", "is_agent")}),
    )


# UserProfileAdmin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username", "user__email")


# AgentAdmin with read-only stats
@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "order_count",
        "total_revenue",
        "average_order_value",
        "sale_leads",
        "no_sale_leads",
    )
    search_fields = ("user__username", "user__email")
    readonly_fields = (
        "order_count",
        "total_revenue",
        "average_order_value",
        "sale_leads",
        "no_sale_leads",
    )

    def order_count(self, obj):
        return obj.get_order_stats()["order_count"]

    order_count.short_description = "Order Count"

    def total_revenue(self, obj):
        return obj.get_order_stats()["total_value"]

    total_revenue.short_description = "Total Revenue"

    def average_order_value(self, obj):
        return obj.get_order_stats()["average_order_value"]

    average_order_value.short_description = "Average Order Value"

    def sale_leads(self, obj):
        return obj.get_lead_conversion_count()["sale"]

    sale_leads.short_description = "Sale Leads"

    def no_sale_leads(self, obj):
        return obj.get_lead_conversion_count()["no_sale"]

    no_sale_leads.short_description = "No Sale Leads"


# Custom Admin Action to Convert Leads
@admin.action(description="Mark selected leads as converted")
def mark_as_converted(modeladmin, request, queryset):
    updated = queryset.update(is_converted=True, conversion_date=timezone.now())
    for lead in queryset.filter(is_converted=True):
        if lead.category and lead.category.name.lower() == "sale":
            Client.objects.get_or_create(
                email=lead.email,
                defaults={
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "age": lead.age,
                    "phone_number": lead.phone_number,
                },
            )
    modeladmin.message_user(
        request,
        f"{updated} lead(s) were successfully marked as converted.",
        messages.SUCCESS,
    )


# LeadAdmin with custom actions
@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "agent",
        "category",
        "is_converted",
        "conversion_date",
        "date_created",
    )
    list_filter = (
        "is_converted",
        "category__name",
        "agent__user__username",
        "date_created",
    )
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "agent__user__username",
    )
    ordering = ("-date_created",)
    readonly_fields = ("conversion_date",)
    actions = [mark_as_converted]


# CategoryAdmin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
