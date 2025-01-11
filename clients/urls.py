from django.urls import path
from .views import (
    ClientListView,
    ClientDetailView,
    ClientUpdateView,
    ClientDeleteView,
    ContactListView,
    ContactCreateView,
    ClientStatisticsView,
    AllClientsStatisticsView,
)

app_name = "clients"

urlpatterns = [
    path("", ClientListView.as_view(), name="client-list"),
    path(
        "all/statistics/",
        AllClientsStatisticsView.as_view(),
        name="all-client-statistics",
    ),
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
        "<str:client_number>/statistics/",
        ClientStatisticsView.as_view(),
        name="client-statistics",
    ),
]
