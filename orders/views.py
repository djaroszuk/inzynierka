# Standard Library Imports
import uuid
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Django Core Imports
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.http import HttpResponseRedirect
from django.utils.http import urlencode
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
from django.core.mail import send_mail
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDay
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.views import generic

# Django Authentication Mixins
from django.contrib.auth.mixins import LoginRequiredMixin

# Custom Mixins
from agents.mixins import OrganisorAndLoginRequiredMixin

# Forms
from .forms import OrderSearchForm
from products.forms import TimeFrameSelectionForm


# Models
from .models import Order, OrderProduct
from products.models import Product
from clients.models import Client, Contact


class OrderListView(LoginRequiredMixin, generic.ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 15  # Set pagination to 15 orders per page

    def get_queryset(self):
        queryset = Order.objects.select_related("client").order_by("-date_created")

        query = self.request.GET.get("q")
        if query:
            try:
                # Filter by exact match if query is a valid integer
                query = int(query)
                queryset = queryset.filter(id=query)
            except ValueError:
                # Ignore non-integer queries
                queryset = queryset.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get paginated queryset
        orders = self.get_queryset()
        paginator = Paginator(orders, self.paginate_by)
        page = self.request.GET.get("page", 1)

        try:
            paginated_orders = paginator.page(page)
        except PageNotAnInteger:
            paginated_orders = paginator.page(1)
        except EmptyPage:
            paginated_orders = paginator.page(paginator.num_pages)

        # Add paginated and searched orders to context
        context["orders"] = paginated_orders
        context["search_form"] = OrderSearchForm(self.request.GET)
        return context

    def post(self, request, *args, **kwargs):
        if request.user.is_organisor and "delete_pending_orders" in request.POST:
            cutoff_time = now() - timedelta(minutes=1)
            pending_orders = Order.objects.filter(
                status="Pending", date_created__lt=cutoff_time
            )

            count = pending_orders.count()
            if count > 0:
                for order in pending_orders:
                    # Restore product quantities and create contact records
                    for order_product in order.order_products.select_related("product"):
                        if order_product.product:
                            order_product.product.stock_quantity += (
                                order_product.quantity
                            )
                            order_product.product.save()

                    Contact.objects.create(
                        client=order.client,
                        reason=Contact.ReasonChoices.SALES_OFFER,
                        description=f"Order #{order.id} was canceled due to inactivity.",
                        contact_date=now(),
                        user=request.user.userprofile,
                    )
                    order.status = "Canceled"
                    order.save()

                messages.success(
                    request,
                    f"{count} pending orders older than 48 hours were canceled, stock was restored, and clients notified.",
                )
            else:
                messages.warning(
                    request,
                    "No pending orders older than 48 hours were found to be canceled.",
                )

        return redirect("orders:order-list")


class ClientOrdersView(LoginRequiredMixin, generic.ListView):
    model = Order
    template_name = "orders/client_orders.html"
    context_object_name = "orders"
    paginate_by = 15

    def get_queryset(self):
        # Filter orders by the specific client
        client = get_object_or_404(Client, client_number=self.kwargs["client_number"])
        queryset = Order.objects.filter(client=client).order_by("-date_created")

        # Search functionality (same as in OrderListView)
        query = self.request.GET.get("q")
        if query:
            try:
                query = int(query)  # Filter by exact match if query is an integer
                queryset = queryset.filter(id=query)
            except ValueError:
                queryset = queryset.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add client information to the context
        client = get_object_or_404(Client, client_number=self.kwargs["client_number"])
        context["client"] = client
        context["client_number"] = client.client_number

        # Add paginated orders to context (same as in OrderListView)
        orders = self.get_queryset()
        paginator = Paginator(orders, self.paginate_by)
        page = self.request.GET.get("page", 1)

        try:
            paginated_orders = paginator.page(page)
        except PageNotAnInteger:
            paginated_orders = paginator.page(1)
        except EmptyPage:
            paginated_orders = paginator.page(paginator.num_pages)

        context["orders"] = paginated_orders
        context["search_form"] = OrderSearchForm(self.request.GET)  # Retain search form
        return context


class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_object(self):
        """Retrieve the order based on its primary key."""
        return get_object_or_404(Order, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        """Add parsed status history to the context."""
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        # Parse `changed_at` into datetime objects
        parsed_status_history = []
        for change in order.status_history:
            change["changed_at"] = parse_datetime(change["changed_at"])
            parsed_status_history.append(change)

        # Add parsed status history to the context
        context["status_history"] = parsed_status_history
        return context

    def post(self, request, *args, **kwargs):
        """Handle the 'Mark as Paid' button."""
        order = self.get_object()

        if "mark_as_paid" in request.POST:
            if order.status != "Paid":  # Only update if not already paid
                order.status = "Paid"
                order.save()

                # Send email confirmation
                subject = f"Payment Confirmation for Order #{order.id}"
                message = (
                    f"Dear Client,\n\n"
                    f"We have received your payment for Order #{order.id}. "
                    f"Your total price is: ${order.total_price:.2f}\n"
                    f"Your order will be processed and shipped soon.\n\n"
                    f"Thank you for shopping with us!\n\n"
                    f"Best regards,\n"
                    f"Your Company Name"
                )
                recipient = order.client.email  # Assuming the client has an email field
                send_mail(
                    subject,
                    message,
                    "your-email@example.com",  # From email
                    [recipient],
                    fail_silently=False,
                )

                messages.success(request, f"Order #{order.id} has been marked as Paid.")
            else:
                messages.warning(
                    request, f"Order #{order.id} is already marked as Paid."
                )

        # Redirect back to the same detail page
        return redirect("orders:order-detail", pk=order.pk)


class OrderCreateView(LoginRequiredMixin, generic.CreateView):
    model = Order
    template_name = "orders/order_create.html"
    fields = ["client"]

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

        # Convert discount choices to a list of tuples
        context["discount_choices"] = [
            (key, f"{value * 100:.0f}%")
            for key, value in self.model.DISCOUNT_CHOICES.items()
        ]
        return context

    def form_valid(self, form):
        """Handle creating the order with associated products and a discount."""
        selected_product_ids = self.request.POST.getlist(
            "product"
        )  # Get selected product IDs
        discount = self.request.POST.get("discount", "0")
        discount = self.model.DISCOUNT_CHOICES.get(discount, Decimal("0.00"))

        # Parse quantities tied to selected products
        selected_products = []
        for product_id in selected_product_ids:
            quantity_field = f"quantity_{product_id}"
            quantity = int(self.request.POST.get(quantity_field, 0))
            if quantity > 0:
                selected_products.append((product_id, quantity))

        # Check if at least one product is selected
        if not selected_products:
            messages.error(
                self.request,
                "Please select at least one product and specify a valid quantity.",
            )
            return render(
                self.request, self.template_name, self.get_context_data(form=form)
            )

        # Validate stock for selected products
        for product_id, quantity in selected_products:
            product = get_object_or_404(Product, pk=product_id)
            if product.stock_quantity < quantity:
                messages.error(
                    self.request,
                    f"Insufficient stock for {product.name}. Available: {product.stock_quantity}.",
                )
                return render(
                    self.request, self.template_name, self.get_context_data(form=form)
                )

        # Create the order
        order = form.save(commit=False)
        order.agent = self.request.user.agent
        order.discount = discount * 100  # Save discount as percentage
        order.status = "Pending"
        order.save()

        # Create OrderProduct entries for selected products
        for product_id, quantity in selected_products:
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

        # Create a Contact entry for the order
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
            # Restore product quantities
            for order_product in order.order_products.all():
                product = order_product.product
                if product:
                    product.stock_quantity += order_product.quantity
                    product.save()

            # Delete the order
            order.delete()
            messages.success(
                request,
                "The order has been canceled, and product quantities have been restored.",
            )
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
        token = request.POST.get("token")
        action = request.POST.get("action")

        # Pobierz zamówienie i zweryfikuj token
        order = get_object_or_404(Order, pk=order_id)

        if order.offer_token != token:
            messages.error(request, "Invalid or expired offer link.")
            return redirect("orders:order-list")

        if action == "accept":
            # Akceptacja zamówienia
            order.status = "Accepted"
            order.save()

            # Wyślij e-mail z informacjami o płatności
            self.send_payment_email(order)

            messages.success(
                request, "The offer has been accepted. A payment email has been sent."
            )
        elif action == "deny":
            # Odrzucenie zamówienia
            order.status = "Canceled"
            order.save()

            # Przywrócenie produktów do stanu magazynowego
            for order_product in order.order_products.all():
                product = order_product.product
                product.stock_quantity += order_product.quantity
                product.save()

            messages.success(
                request, "The offer has been denied, and the order has been canceled."
            )
        else:
            messages.error(request, "Invalid action.")

        return redirect("/")

    def send_payment_email(self, order):
        """Wyślij e-mail z informacjami o płatności."""
        subject = f"Payment Details for Order #{order.id}"
        account_number = "0000 0000 0000 0000"
        client_number = (
            order.client.client_number
        )  # Zakładam, że klient ma pole `client_number`
        total_price = order.total_price  # Zakładam, że zamówienie ma pole `total_price`

        message = f"""
        Dear {order.client.first_name},

        Thank you for accepting the offer for your order #{order.id}.

        Please make a payment to the following account number:
        Account Number: {account_number}

        In the payment title, please include:
        Client Number: {client_number}
        Order Number: {order.id}

        Total Amount: {total_price} USD

        Thank you for your business.

        Best regards,
        Your Company Name
        """

        send_mail(
            subject,
            message,
            "from@example.com",  # Twój adres e-mail
            [order.client.email],
            fail_silently=False,
        )


class OrderStatisticsView(OrganisorAndLoginRequiredMixin, generic.TemplateView):
    template_name = "orders/order-statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize the form with GET data
        form = TimeFrameSelectionForm(self.request.GET or None)
        context["form"] = form

        # Determine the selected time frame
        time_frame = form.cleaned_data.get("time_frame") if form.is_valid() else None
        if not time_frame:
            time_frame = datetime.now().strftime(
                "%Y-%m"
            )  # Default to the current month

        # Calculate the start and end dates based on the selected time frame
        if time_frame == "last_30_days":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        else:
            year, month = map(int, time_frame.split("-"))
            start_date = datetime(year, month, 1)
            next_month = month % 12 + 1
            year = year + (1 if next_month == 1 else 0)
            end_date = datetime(year, next_month, 1)

        # Calculate statistics
        total_revenue = Order.objects.total_revenue(
            start_date=start_date, end_date=end_date
        )
        total_products_sold = Order.objects.total_products_sold(
            start_date=start_date, end_date=end_date
        )
        total_orders = Order.objects.filter(
            date_created__gte=start_date, date_created__lt=end_date
        ).count()

        # Get daily revenue for the selected month
        orders = (
            Order.objects.filter(status="Paid")
            .filter(date_created__date__range=[start_date, end_date])
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
        accepted_orders_count = Order.objects.filter(status="Paid").count()
        completion_rate = (
            round((accepted_orders_count / total_orders_count) * 100, 2)
            if total_orders_count > 0
            else 0
        )

        # Consolidate statistics
        context["statistics"] = {
            "total_revenue": total_revenue,
            "total_products_sold": total_products_sold,
            "total_orders": total_orders,
            "completion_rate": completion_rate,
        }
        context["daily_revenue"] = json.dumps(daily_revenue)

        return context
