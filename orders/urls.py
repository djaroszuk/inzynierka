from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path(
        "client/<int:client_id>/create/",
        views.OrderCreateView.as_view(),
        name="order-create",
    ),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path(
        "client/<int:client_id>/orders/",
        views.ClientOrdersView.as_view(),
        name="client-orders",
    ),
]
