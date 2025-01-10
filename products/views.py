from django.urls import reverse_lazy
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from .models import Product
from orders.models import OrderProduct
from .forms import ProductForm, TimeFrameSelectionForm
from orders.forms import StatisticsFilterForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import timedelta, datetime
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from agents.mixins import OrganisorAndLoginRequiredMixin


class ProductListView(LoginRequiredMixin, generic.ListView):
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


class ProductDetailView(LoginRequiredMixin, generic.DetailView):
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


class ProductUpdateView(
    OrganisorAndLoginRequiredMixin, SuccessMessageMixin, generic.UpdateView
):
    model = Product
    form_class = ProductForm
    template_name = "products/product_update.html"
    success_message = "Product updated successfully!"

    def get_success_url(self):
        # Redirect to the updated product's detail page
        return reverse_lazy("products:product-detail", kwargs={"pk": self.object.pk})


class ProductDeleteView(
    OrganisorAndLoginRequiredMixin, SuccessMessageMixin, generic.DeleteView
):
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


class ProductCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_create.html"
    #    success_url = reverse_lazy('products:product-list')
    success_url = reverse_lazy("products:product-list")


class ProductSalesDetailView(OrganisorAndLoginRequiredMixin, generic.ListView):
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
        """Add chart data and pagination to the context."""
        context = super().get_context_data(**kwargs)

        # Handle the filter form
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        # Get filtered sales data
        product_sales = self.get_queryset()
        print(f"Product sales raw data: {product_sales}")

        # Pagination logic
        paginator = Paginator(product_sales, 5)  # Show 10 products per page
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["product_sales"] = page_obj
        context["page_obj"] = page_obj

        # Chart data processing as before
        total_quantity = sum(item["total_quantity_sold"] for item in product_sales)
        total_revenue = sum(item["total_revenue_sold"] for item in product_sales)
        print(f"Total quantity sold: {total_quantity}")
        print(f"Total revenue: {total_revenue}")

        if total_quantity == 0 or total_revenue == 0:
            labels = []
            quantity_data = []
            revenue_data = []
        else:
            sorted_sales = sorted(
                product_sales, key=lambda x: x["total_quantity_sold"], reverse=True
            )
            top_sales = sorted_sales[:5]
            other_sales = sorted_sales[5:]

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

            quantity_data = [
                round((value / total_quantity) * 100, 2) for value in quantity_data
            ]
            revenue_data = [
                round((value / total_revenue) * 100, 2) for value in revenue_data
            ]

        quantity_data = [float(x) for x in quantity_data]
        revenue_data = [float(x) for x in revenue_data]

        context["chart_labels"] = labels
        context["chart_quantity_data"] = quantity_data
        context["chart_revenue_data"] = revenue_data

        return context


class ProductSalesChartView(OrganisorAndLoginRequiredMixin, generic.TemplateView):
    template_name = "products/sales_chart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = TimeFrameSelectionForm(self.request.GET or None)
        context["form"] = form
        return context


def product_sales_data(request):
    # Get the selected time frame from the request
    time_frame = request.GET.get("time_frame", "last_30_days")
    end_date = datetime.now()

    # Calculate the start and end dates based on the selected time frame
    if time_frame == "last_30_days":
        start_date = end_date - timedelta(days=30)
    else:
        year, month = map(int, time_frame.split("-"))
        start_date = datetime(year, month, 1)
        next_month = month % 12 + 1
        year = year + (1 if next_month == 1 else 0)
        end_date = datetime(year, next_month, 1)

    # Fetch sales data for the selected time frame
    sales_data = (
        OrderProduct.objects.filter(
            order__status="Paid", order__date_created__range=(start_date, end_date)
        )
        .values("product_name")
        .annotate(
            total_sold=Sum("quantity"),
            unique_customers=Count("order__client", distinct=True),
        )
        .order_by("-total_sold")[:5]
    )

    # Prepare data for the chart
    labels = [entry["product_name"] for entry in sales_data]
    total_sold = [entry["total_sold"] for entry in sales_data]
    unique_customers = [entry["unique_customers"] for entry in sales_data]

    return JsonResponse(
        {
            "labels": labels,
            "total_sold": total_sold,
            "unique_customers": unique_customers,
        }
    )
