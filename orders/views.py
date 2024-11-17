from django.views import generic, View
from django.shortcuts import get_object_or_404, redirect, render
from .models import Order, OrderProduct
from .forms import OrderForm, OrderProductFormSet
from clients.models import Client


class OrderListView(generic.ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return Order.objects.select_related("client").all()


class OrderDetailView(generic.DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        order_products = OrderProduct.objects.filter(order=order).select_related(
            "product"
        )

        # Calculate totals for each product and overall total
        product_totals = [
            {
                "product": item.product,
                "quantity": item.quantity,
                "total": item.product.price * item.quantity,
            }
            for item in order_products
        ]
        total_price = sum(item["total"] for item in product_totals)

        context["order_products"] = product_totals
        context["total_price"] = total_price
        return context


class OrderCreateView(View):
    def get(self, request, client_id):
        client = get_object_or_404(Client, pk=client_id)
        order_form = OrderForm(initial={"client": client})
        formset = OrderProductFormSet(queryset=OrderProduct.objects.none())
        return render(
            request,
            "orders/order_create.html",
            {"order_form": order_form, "formset": formset},
        )

    def post(self, request, client_id):
        client = get_object_or_404(Client, pk=client_id)
        order_form = OrderForm(request.POST)
        formset = OrderProductFormSet(request.POST)

        if order_form.is_valid() and formset.is_valid():
            # Save Order
            order = order_form.save(commit=False)
            order.client = client
            order.save()

            # Save OrderProduct items
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    order_product = form.save(commit=False)
                    order_product.order = order
                    order_product.save()

            return redirect(
                "clients:client-detail", pk=client.id
            )  # Redirect to client detail page

        return render(
            request,
            "orders/order_create.html",
            {"order_form": order_form, "formset": formset},
        )


class ClientOrdersView(generic.ListView):
    model = Order
    template_name = "orders/client_orders.html"
    context_object_name = "orders"

    def get_queryset(self):
        # Get the client by client_id from the URL
        client = get_object_or_404(Client, pk=self.kwargs["client_id"])

        # Filter orders by the client
        return Order.objects.filter(client=client)
