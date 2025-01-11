# Django imports
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

# Application-specific imports
from .models import Product
from orders.models import OrderProduct
from .forms import ProductForm, TimeFrameSelectionForm
from orders.forms import StatisticsFilterForm
from agents.mixins import OrganisorAndLoginRequiredMixin

# Python standard library imports
from datetime import timedelta, datetime


# View for listing products with pagination
class ProductListView(LoginRequiredMixin, generic.ListView):
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 10  # Number of items per page

    def get_queryset(self):
        # Retrieve all products ordered by name
        return Product.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        # Add pagination data to the context
        context = super().get_context_data(**kwargs)
        products = self.get_queryset()
        paginator = Paginator(products, self.paginate_by)
        page = self.request.GET.get("page", 1)

        try:
            paginated_products = paginator.page(page)
        except PageNotAnInteger:
            paginated_products = paginator.page(1)
        except EmptyPage:
            paginated_products = paginator.page(paginator.num_pages)

        context["products"] = paginated_products
        return context


# View for displaying detailed product information
class ProductDetailView(LoginRequiredMixin, generic.DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        # Add price history data to the context
        context = super().get_context_data(**kwargs)
        context["price_history"] = self.object.price_history.all().order_by(
            "-changed_at"
        )
        return context


# View for updating product information
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


# View for deleting a product
class ProductDeleteView(
    OrganisorAndLoginRequiredMixin, SuccessMessageMixin, generic.DeleteView
):
    model = Product
    template_name = "products/product_delete.html"
    success_url = reverse_lazy("products:product-list")
    success_message = "Product deleted successfully!"

    def get_context_data(self, **kwargs):
        # Add cancel URL to the context for returning to the product detail page
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy(
            "products:product-detail", kwargs={"pk": self.object.pk}
        )
        return context


# View for creating a new product
class ProductCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_create.html"
    success_url = reverse_lazy("products:product-list")


# View for displaying product sales details with filtering and chart data
class ProductSalesDetailView(OrganisorAndLoginRequiredMixin, generic.ListView):
    template_name = "products/product_sales_detail.html"
    context_object_name = "product_sales"

    def get_queryset(self):
        # Retrieve aggregated product sales data, optionally filtered by date
        form = StatisticsFilterForm(self.request.GET or None)
        if form.is_valid():
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")
            return OrderProduct.get_product_sales(
                start_date=start_datetime, end_date=end_datetime
            )
        return OrderProduct.get_product_sales()

    def get_context_data(self, **kwargs):
        # Add chart data and pagination to the context
        context = super().get_context_data(**kwargs)
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form
        product_sales = self.get_queryset()
        paginator = Paginator(product_sales, 5)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["product_sales"] = page_obj
        context["page_obj"] = page_obj

        total_quantity = sum(item["total_quantity_sold"] for item in product_sales)
        total_revenue = sum(item["total_revenue_sold"] for item in product_sales)

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

            quantity_data = [
                round((value / total_quantity) * 100, 2) for value in quantity_data
            ]
            revenue_data = [
                round((value / total_revenue) * 100, 2) for value in revenue_data
            ]

        context["chart_labels"] = labels
        context["chart_quantity_data"] = quantity_data
        context["chart_revenue_data"] = revenue_data

        return context


# View for displaying sales chart
class ProductSalesChartView(OrganisorAndLoginRequiredMixin, generic.TemplateView):
    template_name = "products/sales_chart.html"

    def get_context_data(self, **kwargs):
        # Add the time frame selection form to the context
        context = super().get_context_data(**kwargs)
        form = TimeFrameSelectionForm(self.request.GET or None)
        context["form"] = form
        return context


# API endpoint for fetching product sales data
def product_sales_data(request):
    time_frame = request.GET.get("time_frame", "last_30_days")
    end_date = datetime.now()

    if time_frame == "last_30_days":
        start_date = end_date - timedelta(days=30)
    else:
        year, month = map(int, time_frame.split("-"))
        start_date = datetime(year, month, 1)
        next_month = month % 12 + 1
        year = year + (1 if next_month == 1 else 0)
        end_date = datetime(year, next_month, 1)

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
