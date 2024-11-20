# clients/urls.py
from django.urls import path
from .views import (
    ClientListView,
    ClientDetailView,
    ClientCreateView,
    ClientUpdateView,
    ClientDeleteView,
)

app_name = "clients"

urlpatterns = [
    path("", ClientListView.as_view(), name="client-list"),
    path("<str:client_number>/", ClientDetailView.as_view(), name="client-detail"),
    path("create/", ClientCreateView.as_view(), name="client-create"),
    path(
        "<str:client_number>/update/", ClientUpdateView.as_view(), name="client-update"
    ),
    path(
        "<str:client_number>/delete/", ClientDeleteView.as_view(), name="client-delete"
    ),
]
