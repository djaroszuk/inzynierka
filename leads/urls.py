from django.urls import path
from .views import (
    LeadListView,
    LeadDetailView,
    LeadCreateView,
    LeadUpdateView,
    LeadDeleteView,
    LeadCategoryUpdateView,
    LeadUploadView,
)

app_name = "leads"

urlpatterns = [
    path("", LeadListView.as_view(), name="lead-list"),
    path("<int:pk>/", LeadDetailView.as_view(), name="lead-detail"),
    path("new/", LeadCreateView.as_view(), name="lead-create"),
    path("<int:pk>/edit/", LeadUpdateView.as_view(), name="lead-update"),
    path("<int:pk>/delete/", LeadDeleteView.as_view(), name="lead-delete"),
    path(
        "<int:pk>/category/",
        LeadCategoryUpdateView.as_view(),
        name="lead-category-update",
    ),
    path("upload/", LeadUploadView.as_view(), name="lead-upload"),
]
