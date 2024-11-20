from django.views import generic
from django.shortcuts import get_object_or_404
from .models import Order, OrderProduct
from django.contrib.auth.mixins import LoginRequiredMixin
from products.models import Product
from clients.models import Client
from django.urls import reverse_lazy


class OrderListView(generic.ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return Order.objects.select_related("client").all()


class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_object(self):
        """Retrieve the order based on its primary key."""
        # Fetch the specific order without additional filtering
        return get_object_or_404(Order, pk=self.kwargs["pk"])


class OrderCreateView(LoginRequiredMixin, generic.CreateView):
    model = Order
    template_name = "orders/order_create.html"
    fields = [
        "client"
    ]  # Only client field in the form (this can be pre-filled if needed)
    success_url = reverse_lazy("orders:order-list")

    def get_context_data(self, **kwargs):
        """Add the list of products to the context."""
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.all()  # Fetch all products
        return context

    def form_valid(self, form):
        """Override form_valid to handle creating associated OrderProduct instances."""
        order = form.save()  # Save the order first

        # Handle creating OrderProduct entries after saving the order
        product_ids = self.request.POST.getlist("product")  # Get selected products
        quantities = self.request.POST.getlist("quantity")  # Get selected quantities

        for product_id, quantity in zip(product_ids, quantities):
            product = get_object_or_404(Product, pk=product_id)
            OrderProduct.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                product_name=product.name,
                product_price=product.price,
            )

        return super().form_valid(form)


class ClientOrdersView(generic.ListView):
    model = Order
    template_name = "orders/client_orders.html"
    context_object_name = "orders"

    def get_queryset(self):
        # Get the client by client_id from the URL
        client = get_object_or_404(Client, client_number=self.kwargs["client_number"])

        # Filter orders by the client
        return Order.objects.filter(client=client)
