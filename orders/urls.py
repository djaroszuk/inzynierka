from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path(
        "create/",
        views.OrderCreateView.as_view(),
        name="order-create",
    ),
    path("summary/<int:pk>/", views.OrderSummaryView.as_view(), name="order-summary"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path(
        "client/<str:client_number>/orders/",
        views.ClientOrdersView.as_view(),
        name="client-orders",
    ),
    path("statistics/", views.OrderStatisticsView.as_view(), name="order-statistics"),
    path(
        "statistics/product_sales/",
        views.ProductSalesDetailView.as_view(),
        name="product-sales-detail",
    ),
    path(
        "<int:order_id>/confirm/",
        views.OrderConfirmView.as_view(),
        name="order_confirm",
    ),
]
