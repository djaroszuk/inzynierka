from django.urls import path
from .views import (
    ProductCreateView,
    AddProductsToClientView,
    ClientProductsView,
    ProductUpdateView,
    ProductDetailView,
    ProductDeleteView,
    ProductListView,
)

app_name = "products"

urlpatterns = [
    path("", ProductListView.as_view(), name="product-list"),
    path("create/", ProductCreateView.as_view(), name="product-create"),
    path(
        "client/<int:client_id>/products/",
        ClientProductsView.as_view(),
        name="client-products",
    ),
    path(
        "client/<int:client_id>/add-products/",
        AddProductsToClientView.as_view(),
        name="add-products",
    ),
    path("<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("<int:pk>/update/", ProductUpdateView.as_view(), name="product-update"),
    path("<int:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"),
]
