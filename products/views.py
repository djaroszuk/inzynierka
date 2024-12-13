from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from .models import Product
from orders.models import OrderProduct
from .forms import ProductForm, AddProductForm
from clients.models import Client


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
        # Get the total quantity of each product sold (snapshot of product name)
        return OrderProduct.get_product_sales()
