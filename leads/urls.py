from django.urls import path
from .views import (
    LeadListView,
    LeadDetailView,
    LeadCreateView,
    LeadUpdateView,
    LeadDeleteView,
)

app_name = "leads"

urlpatterns = [
    path("", LeadListView.as_view(), name="lead_list"),
    path("lead/<int:pk>/", LeadDetailView.as_view(), name="lead_detail"),
    path("lead/new/", LeadCreateView.as_view(), name="create_lead"),
    path("lead/<int:pk>/edit/", LeadUpdateView.as_view(), name="update_lead"),
    path("lead/<int:pk>/delete/", LeadDeleteView.as_view(), name="delete_lead"),
]
