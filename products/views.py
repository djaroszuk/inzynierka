from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from .models import Product
from orders.models import OrderProduct
from .forms import ProductForm, AddProductForm
from clients.models import Client
from orders.forms import StatisticsFilterForm


class ProductListView(generic.ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"


class ProductDetailView(generic.DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"


class ProductUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_update.html"
    success_url = reverse_lazy("products:product-list")
    success_message = "Product updated successfully!"


class ProductDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Product
    template_name = "products/product_delete.html"
    success_url = reverse_lazy("products:product-list")
    success_message = "Product deleted successfully!"


class ProductCreateView(generic.CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_create.html"
    #    success_url = reverse_lazy('products:product-list')
    success_url = reverse_lazy("products:product-list")


class ClientProductsView(generic.TemplateView):
    template_name = "products/client_products.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = get_object_or_404(Client, client_number=self.kwargs["client_number"])
        context["client"] = client
        context["products"] = (
            client.products.all()
        )  # Products associated with the client
        return context


class AddProductsToClientView(generic.FormView):
    template_name = "products/add_products_to_client.html"
    form_class = AddProductForm

    def form_valid(self, form):
        client = get_object_or_404(Client, client_number=self.kwargs["client_number"])
        products = form.cleaned_data["products"]
        client.products.add(
            *products
        )  # Associate the selected products with the client
        return redirect(
            reverse_lazy(
                "products:client-products",
                kwargs={"client_number": client.client_number},
            )
        )


class ProductSalesDetailView(generic.ListView):
    template_name = "products/product_sales_detail.html"
    context_object_name = "product_sales"

    def get_queryset(self):
        """Retrieve aggregated product sales data, optionally filtered by date."""
        form = StatisticsFilterForm(self.request.GET or None)
        if form.is_valid():
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")
            return OrderProduct.get_product_sales(
                start_date=start_datetime, end_date=end_datetime
            )
        return OrderProduct.get_product_sales()

    def get_context_data(self, **kwargs):
        """Add chart data to the context."""
        context = super().get_context_data(**kwargs)

        # Handle the filter form
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        # Get filtered sales data
        product_sales = self.get_queryset()

        # Calculate total products sold and total revenue
        total_quantity = sum(item["total_quantity_sold"] for item in product_sales)
        total_revenue = sum(item["total_revenue_sold"] for item in product_sales)

        if total_quantity == 0 or total_revenue == 0:
            labels = []
            quantity_data = []
            revenue_data = []
        else:
            labels = [item["product_name"] for item in product_sales]
            quantity_data = [
                round((item["total_quantity_sold"] / total_quantity) * 100, 2)
                for item in product_sales
            ]
            revenue_data = [
                round((item["total_revenue_sold"] / total_revenue) * 100, 2)
                for item in product_sales
            ]

        # **Convert Decimal to float**
        quantity_data = [float(x) for x in quantity_data]
        revenue_data = [float(x) for x in revenue_data]

        # Pass raw data to the template; json_script will handle serialization
        context["chart_labels"] = labels
        context["chart_quantity_data"] = quantity_data
        context["chart_revenue_data"] = revenue_data

        return context
