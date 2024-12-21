from django.views import generic
from django.shortcuts import get_object_or_404
from .models import Order, OrderProduct
from django.contrib.auth.mixins import LoginRequiredMixin
from products.models import Product
from clients.models import Client, Contact
from datetime import datetime
from .forms import StatisticsFilterForm
from django.shortcuts import redirect, render, reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.http import urlencode
from django.contrib.sites.shortcuts import get_current_site
import uuid
from django.core.mail import send_mail
from django.utils.timezone import now
from django.db.models.functions import TruncDay
from django.db.models import Count, Sum, F
import json
from decimal import Decimal


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
    fields = ["client"]

    DISCOUNT_CHOICES = {
        "0": Decimal("0.00"),  # No discount
        "5": Decimal("0.05"),
        "10": Decimal("0.10"),
        "15": Decimal("0.15"),
    }

    def get_initial(self):
        """Set the initial value for the client field."""
        initial = super().get_initial()
        client_number = self.request.GET.get("client_number")
        if client_number:
            try:
                client = Client.objects.get(client_number=client_number)
                initial["client"] = client
            except Client.DoesNotExist:
                messages.warning(
                    self.request,
                    "Invalid client number provided. Please choose a valid client.",
                )
        return initial

    def get_context_data(self, **kwargs):
        """Add the list of products and discount options to the context."""
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.all()
        context["discount_choices"] = [0, 5, 10, 15]  # Discount options
        return context

    def form_valid(self, form):
        """Handle creating the order with associated products and a discount."""
        product_ids = self.request.POST.getlist("product")
        quantities = self.request.POST.getlist("quantity")
        discount = self.request.POST.get("discount", "0")  # Default discount to 0
        discount = self.DISCOUNT_CHOICES.get(discount, Decimal("0.00"))

        # Convert quantities to integers
        quantities = [int(q) for q in quantities]

        if not product_ids or not any(q > 0 for q in quantities):
            messages.error(
                self.request,
                "Please select at least one product and specify a valid quantity.",
            )
            return render(
                self.request, self.template_name, self.get_context_data(form=form)
            )

        for product_id, quantity in zip(product_ids, quantities):
            product = get_object_or_404(Product, pk=product_id)
            if product.stock_quantity < quantity:
                messages.error(
                    self.request,
                    f"Insufficient stock for {product.name}. Available: {product.stock_quantity}.",
                )
                return render(
                    self.request, self.template_name, self.get_context_data(form=form)
                )

        order = form.save(commit=False)
        order.agent = self.request.user.agent
        order.discount = discount * 100  # Save discount as percentage
        order.status = "Pending"
        order.save()

        for product_id, quantity in zip(product_ids, quantities):
            if quantity > 0:
                product = get_object_or_404(Product, pk=product_id)
                product.stock_quantity -= quantity
                product.save()

                # Create the OrderProduct with discounted price
                OrderProduct.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    product_name=product.name,
                    product_price=None,  # Let the `save` method calculate discounted price
                )

        Contact.objects.create(
            client=order.client,
            reason=Contact.ReasonChoices.SALES_OFFER,
            description=f"Order #{order.id} was sent to the client.",
            contact_date=now(),
            user=self.request.user.userprofile,
        )

        return HttpResponseRedirect(
            reverse("orders:order-summary", kwargs={"pk": order.pk})
        )


class OrderSummaryView(LoginRequiredMixin, generic.DetailView):
    model = Order
    template_name = "orders/order_summary.html"

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        action = request.POST.get("action")

        if action == "send_offer":
            # Generate a unique token for the link
            token = str(uuid.uuid4())
            order.offer_token = token  # Save the token in the order model (you should add this field to your model)
            order.save()

            # # Send email to the client with a link to accept or deny
            subject = f"Offer for Order #{order.id}"
            message = f"""
                Dear {order.client.first_name},

                An offer has been made for your order #{order.id}. To review and either accept or deny the offer, please click the link below:

                {self.get_order_confirmation_url(order, token)}

                If you have any questions, please contact us.

                Best regards,
                Your Company Name
            """
            send_mail(
                subject,
                message,
                "from@example.com",  # Replace with your email
                [order.client.email],
                fail_silently=False,
            )
            # Instead of sending an email, print the link to the console
            offer_url = self.get_order_confirmation_url(order, token)
            print(f"Mock email sent to {order.client.email} with the link: {offer_url}")

            messages.success(request, "The offer has been sent to the client.")
            return redirect("orders:order-list")

        elif action == "cancel":
            order.delete()
            messages.success(request, "The order has been canceled and deleted.")
            return redirect("orders:order-list")

        messages.error(request, "Invalid action.")
        return redirect("orders:order-summary", pk=order.pk)

    def get_order_confirmation_url(self, order, token):
        # Generate the link that the client will click to accept or deny the offer
        domain = get_current_site(self.request).domain
        path = reverse("orders:order_confirm", kwargs={"order_id": order.id})
        query = urlencode({"token": token})
        return f"http://{domain}{path}?{query}"


class OrderConfirmView(generic.View):
    def get(self, request, *args, **kwargs):
        order_id = kwargs["order_id"]
        token = request.GET.get("token")

        # Get the order based on the ID and check if the token matches
        order = get_object_or_404(Order, pk=order_id)

        # Check if the token matches the one stored in the order
        if order.offer_token != token:
            messages.error(request, "Invalid or expired offer link.")
            return redirect("orders:order-list")

        return render(request, "orders/order_confirm.html", {"order": order})

    def post(self, request, *args, **kwargs):
        order_id = kwargs["order_id"]
        action = request.POST.get("action")
        token = request.POST.get("token")

        # Get the order and validate the token
        order = get_object_or_404(Order, pk=order_id)

        if order.offer_token != token:
            messages.error(request, "Invalid or expired offer link.")
            return redirect("orders:order-list")

        if action == "accept":
            # Accept the offer and change the order status
            order.status = "Accepted"
            order.save()
            messages.success(request, "You have accepted the offer.")

            # Create a Contact instance for follow-up
            Contact.objects.create(
                client=order.client,  # Link the contact to the order's client
                reason=Contact.ReasonChoices.FOLLOW_UP,  # Set reason to "Follow-up"
                description=f"Order #{order.id} was accepted.",  # Description mentioning acceptance
                contact_date=now(),  # Automatically set to the current date and time
                user=request.user.userprofile,  # Assuming the user has a UserProfile
            )
        elif action == "deny":
            # Deny the offer and delete the order
            order.status = "Canceled"
            order.save()
            # Return the products to stock
            for order_product in order.order_products.all():
                product = order_product.product
                product.stock_quantity += (
                    order_product.quantity
                )  # Increase the stock by the quantity ordered
                product.save()  # Save the product with the updated stock

            messages.success(
                request, "You have denied the offer and the order has been canceled."
            )
        else:
            messages.error(request, "Invalid action.")

        return redirect("orders:order-list")


class ClientOrdersView(generic.ListView):
    model = Order
    template_name = "orders/client_orders.html"
    context_object_name = "orders"

    def get_queryset(self):
        # Get the client by client_id from the URL
        client = get_object_or_404(Client, client_number=self.kwargs["client_number"])

        # Filter orders by the client
        return Order.objects.filter(client=client)

    def get_context_data(self, **kwargs):
        # Add client information to the context for use in the template
        context = super().get_context_data(**kwargs)
        client = get_object_or_404(Client, client_number=self.kwargs["client_number"])
        context["client"] = client  # Add the client object to the context
        context["client_number"] = client.client_number  # Add client_number explicitly
        return context


class OrderStatisticsView(generic.TemplateView):
    template_name = "orders/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize the form with GET data
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        # Initialize filtering variables
        start_datetime = None
        end_datetime = None

        if form.is_valid():
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")

        # Calculate statistics
        total_revenue = Order.objects.total_revenue(
            start_date=start_datetime, end_date=end_datetime
        )
        total_products_sold = Order.objects.total_products_sold(
            start_date=start_datetime, end_date=end_datetime
        )
        total_orders = Order.objects.filter(
            date_created__gte=start_datetime if start_datetime else datetime.min,
            date_created__lte=end_datetime if end_datetime else datetime.max,
        ).count()

        # Get daily revenue for the current month
        today = now().date()
        start_date = today.replace(day=1)  # First day of the current month
        orders = (
            Order.objects.filter(status="Accepted")
            .filter(date_created__date__range=[start_date, today])
            .annotate(day=TruncDay("date_created"))
            .values("day")
            .annotate(
                total_revenue=Sum(
                    F("order_products__product_price") * F("order_products__quantity")
                ),
                total_orders=Count("id"),
            )
            .order_by("day")
        )

        daily_revenue = [
            {
                "date": entry["day"].strftime("%Y-%m-%d"),
                "total_revenue": float(entry["total_revenue"] or 0),
                "total_orders": entry["total_orders"],
            }
            for entry in orders
        ]

        # Calculate order completion rate
        total_orders_count = Order.objects.count()
        accepted_orders_count = Order.objects.filter(status="Accepted").count()
        completion_rate = (
            (accepted_orders_count / total_orders_count) * 100
            if total_orders_count > 0
            else 0
        )

        # Update context
        context["statistics"] = {
            "total_revenue": total_revenue,
            "total_products_sold": total_products_sold,
            "total_orders": total_orders,
        }
        context["daily_revenue"] = json.dumps(daily_revenue)
        context["completion_rate"] = completion_rate
        context["accepted_orders"] = accepted_orders_count
        context["remaining_orders"] = total_orders_count - accepted_orders_count
        context["total_orders_count"] = total_orders_count

        return context
