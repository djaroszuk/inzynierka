from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from .models import Product
from orders.models import OrderProduct
from .forms import ProductForm, AddProductForm
from clients.models import Client
from orders.forms import StatisticsFilterForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


class ProductListView(generic.ListView):
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 10  # Number of items per page

    def get_queryset(self):
        """Return all products ordered by name."""
        return Product.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        """Add pagination to the context."""
        context = super().get_context_data(**kwargs)

        # Get the paginated queryset
        products = self.get_queryset()
        paginator = Paginator(products, self.paginate_by)
        page = self.request.GET.get("page", 1)

        try:
            paginated_products = paginator.page(page)
        except PageNotAnInteger:
            paginated_products = paginator.page(1)
        except EmptyPage:
            paginated_products = paginator.page(paginator.num_pages)

        context["products"] = paginated_products  # Add paginated products to context
        return context


class ProductDetailView(generic.DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the price history to the context
        context["price_history"] = self.object.price_history.all().order_by(
            "-changed_at"
        )
        return context


class ProductUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_update.html"
    success_message = "Product updated successfully!"

    def get_success_url(self):
        # Redirect to the updated product's detail page
        return reverse_lazy("products:product-detail", kwargs={"pk": self.object.pk})


class ProductDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Product
    template_name = "products/product_delete.html"
    success_url = reverse_lazy("products:product-list")
    success_message = "Product deleted successfully!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Set cancel_url to the product's detail page
        context["cancel_url"] = reverse_lazy(
            "products:product-detail", kwargs={"pk": self.object.pk}
        )
        return context


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
            print(f"Filtering data from {start_datetime} to {end_datetime}")
            return OrderProduct.get_product_sales(
                start_date=start_datetime, end_date=end_datetime
            )
        print("No date filters applied")
        return OrderProduct.get_product_sales()

    def get_context_data(self, **kwargs):
        """Add chart data to the context."""
        context = super().get_context_data(**kwargs)

        # Handle the filter form
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        # Get filtered sales data
        product_sales = self.get_queryset()
        print(f"Product sales raw data: {product_sales}")

        # Calculate total products sold and total revenue
        total_quantity = sum(item["total_quantity_sold"] for item in product_sales)
        total_revenue = sum(item["total_revenue_sold"] for item in product_sales)
        print(f"Total quantity sold: {total_quantity}")
        print(f"Total revenue: {total_revenue}")

        if total_quantity == 0 or total_revenue == 0:
            labels = []
            quantity_data = []
            revenue_data = []
        else:
            # Sort by total quantity sold and take top 5
            sorted_sales = sorted(
                product_sales, key=lambda x: x["total_quantity_sold"], reverse=True
            )
            top_sales = sorted_sales[:5]
            other_sales = sorted_sales[5:]

            # Aggregate the "Other" category
            other_quantity = sum(item["total_quantity_sold"] for item in other_sales)
            other_revenue = sum(item["total_revenue_sold"] for item in other_sales)

            labels = [item["product_name"] for item in top_sales]
            quantity_data = [item["total_quantity_sold"] for item in top_sales]
            revenue_data = [item["total_revenue_sold"] for item in top_sales]

            if other_sales:
                labels.append("Other")
                quantity_data.append(other_quantity)
                revenue_data.append(other_revenue)

            print(f"Top products: {labels}")
            print(f"Quantities: {quantity_data}")
            print(f"Revenues: {revenue_data}")

            # Convert data to percentages
            quantity_data = [
                round((value / total_quantity) * 100, 2) for value in quantity_data
            ]
            revenue_data = [
                round((value / total_revenue) * 100, 2) for value in revenue_data
            ]

        # **Convert Decimal to float**
        quantity_data = [float(x) for x in quantity_data]
        revenue_data = [float(x) for x in revenue_data]

        # Pass raw data to the template; json_script will handle serialization
        context["chart_labels"] = labels
        context["chart_quantity_data"] = quantity_data
        context["chart_revenue_data"] = revenue_data

        # Debug final chart data
        print(f"Chart labels: {labels}")
        print(f"Chart quantity data: {quantity_data}")
        print(f"Chart revenue data: {revenue_data}")

        return context
