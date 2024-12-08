# clients/urls.py
from django.urls import path
from .views import (
    ClientListView,
    ClientDetailView,
    ClientUpdateView,
    ClientDeleteView,
    ContactListView,
    ContactCreateView,
    ClientStatisticsView,
)

app_name = "clients"

urlpatterns = [
    path("", ClientListView.as_view(), name="client-list"),
    path("<str:client_number>/", ClientDetailView.as_view(), name="client-detail"),
    path(
        "<str:client_number>/update/", ClientUpdateView.as_view(), name="client-update"
    ),
    path(
        "<str:client_number>/delete/", ClientDeleteView.as_view(), name="client-delete"
    ),
    path(
        "<str:client_number>/contacts/", ContactListView.as_view(), name="contact-list"
    ),
    path(
        "<str:client_number>/contacts/new/",
        ContactCreateView.as_view(),
        name="contact-create",
    ),
    path(
        "client/<str:client_number>/statistics/",
        ClientStatisticsView.as_view(),
        name="client-statistics",
    ),
]
