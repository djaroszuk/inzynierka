# Standard Library Imports
import uuid
import json
import csv
from datetime import datetime, timedelta
from decimal import Decimal

# Django Core Imports
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.http import HttpResponseRedirect, HttpResponse
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
from django.conf import settings

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


# Handles listing and filtering orders
class OrderListView(LoginRequiredMixin, generic.ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 15  # Number of orders per page

    def get_queryset(self):
        # Returns orders sorted by creation date, filtered by query
        queryset = Order.objects.select_related("client").order_by("-date_created")

        query = self.request.GET.get("q")
        if query:
            try:
                query = int(query)  # Match exact order ID if the query is an integer
                queryset = queryset.filter(id=query)
            except ValueError:
                queryset = queryset.none()  # Ignore non-integer queries

        return queryset

    def get_context_data(self, **kwargs):
        # Adds search form and paginated orders to the context
        context = super().get_context_data(**kwargs)
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
        context["search_form"] = OrderSearchForm(self.request.GET)
        return context

    def get(self, request, *args, **kwargs):
        # Handles exporting orders to CSV if requested
        if request.GET.get("export") == "csv":
            return self.export_to_csv()
        return super().get(request, *args, **kwargs)

    def export_to_csv(self):
        # Exports orders to a CSV file
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders.csv"'

        writer = csv.writer(response)
        writer.writerow(["Order ID", "Client", "Status", "Date Created", "Total Price"])

        orders = self.get_queryset()
        for order in orders:
            writer.writerow(
                [
                    order.id,
                    f"{order.client.first_name} {order.client.last_name}",
                    order.status,
                    order.date_created,
                    order.total_price,
                ]
            )

        return response

    def post(self, request, *args, **kwargs):
        # Handles bulk cancellation of pending orders older than 48 hours
        if request.user.is_organisor and "delete_pending_orders" in request.POST:
            cutoff_time = now() - timedelta(minutes=1)
            pending_orders = Order.objects.filter(
                status="Pending", date_created__lt=cutoff_time
            )

            count = pending_orders.count()
            if count > 0:
                for order in pending_orders:
                    # Restore product stock and notify clients
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
                    f"{count} pending orders older than 48 hours were canceled, stock restored, and clients notified.",
                )
            else:
                messages.warning(
                    request,
                    "No pending orders older than 48 hours were found to be canceled.",
                )

        return redirect("orders:order-list")


# Displays orders for a specific client
class ClientOrdersView(LoginRequiredMixin, generic.ListView):
    model = Order
    template_name = "orders/client_orders.html"
    context_object_name = "orders"
    paginate_by = 15  # Number of orders per page

    def get_queryset(self):
        # Filters orders by the client associated with the given client_number
        client = get_object_or_404(Client, client_number=self.kwargs["client_number"])
        queryset = Order.objects.filter(client=client).order_by("-date_created")

        query = self.request.GET.get("q")
        if query:
            try:
                query = int(query)  # Match exact order ID if the query is an integer
                queryset = queryset.filter(id=query)
            except ValueError:
                queryset = queryset.none()  # Ignore non-integer queries

        return queryset

    def get_context_data(self, **kwargs):
        # Adds client information and paginated orders to the context
        context = super().get_context_data(**kwargs)
        client = get_object_or_404(Client, client_number=self.kwargs["client_number"])
        context["client"] = client
        context["client_number"] = client.client_number

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
        context["search_form"] = OrderSearchForm(self.request.GET)
        return context

    def get(self, request, *args, **kwargs):
        # Handles exporting client orders to CSV if requested
        if request.GET.get("export") == "csv":
            return self.export_to_csv()
        return super().get(request, *args, **kwargs)

    def export_to_csv(self):
        # Exports client orders to a CSV file
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="client_orders.csv"'

        writer = csv.writer(response)
        writer.writerow(["Order ID", "Client", "Status", "Date Created", "Total Price"])

        orders = self.get_queryset()
        for order in orders:
            writer.writerow(
                [
                    order.id,
                    f"{order.client.first_name} {order.client.last_name}",
                    order.status,
                    order.date_created,
                    order.total_price,
                ]
            )

        return response


# Displays details for a specific order
class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_object(self):
        # Retrieves the order by its primary key
        return get_object_or_404(Order, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        # Adds parsed status history to the context
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        parsed_status_history = []
        for change in order.status_history:
            change["changed_at"] = parse_datetime(change["changed_at"])
            parsed_status_history.append(change)

        context["status_history"] = parsed_status_history
        return context

    def post(self, request, *args, **kwargs):
        # Handles marking the order as paid or canceling the order
        order = self.get_object()

        if "mark_as_paid" in request.POST:
            if order.status != "Paid":
                order.status = "Paid"
                order.save()

                subject = f"Payment Confirmation for Order #{order.id}"
                message = (
                    f"Dear Client,\n\n"
                    f"We have received your payment for Order #{order.id}. "
                    f"Your total price is: ${order.total_price:.2f}\n"
                    f"Your order will be processed and shipped soon.\n\n"
                    f"Thank you for shopping with us!\n\n"
                    f"Best regards,\n"
                    f"Dominik Jaroszuk CRM"
                )
                recipient = order.client.email
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [recipient],
                    fail_silently=False,
                )

                messages.success(request, f"Order #{order.id} has been marked as Paid.")
            else:
                messages.warning(
                    request, f"Order #{order.id} is already marked as Paid."
                )

        elif "cancel_order" in request.POST:
            if order.status == "Paid":
                messages.error(
                    request,
                    f"Order #{order.id} cannot be canceled because it has already been completed (status: Paid).",
                )
            elif order.status == "Canceled":
                messages.warning(request, f"Order #{order.id} is already canceled.")
            else:
                # Restore stock for each product in the order
                for order_product in order.order_products.all():
                    product = order_product.product
                    if product:
                        product.stock_quantity += order_product.quantity
                        product.save()

                # Update the order status and save changes
                order.status = "Canceled"
                order.save()

                # Create a contact entry for the canceled order
                Contact.objects.create(
                    client=order.client,
                    reason=Contact.ReasonChoices.SALES_OFFER,
                    description=f"Order #{order.id} was canceled due to the client's request.",
                    contact_date=now(),
                    user=request.user.userprofile,
                )

                # Send cancellation confirmation email to the client
                subject = f"Order #{order.id} Cancellation Confirmation"
                message = (
                    f"Dear Client,\n\n"
                    f"Your Order #{order.id} has been successfully canceled as per your request.\n"
                    f"If you have any questions, please contact our support team.\n\n"
                    f"Best regards,\n"
                    f"Dominik Jaroszuk CRM"
                )
                recipient = order.client.email
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,  # Replace with a valid email address
                    [recipient],
                    fail_silently=False,
                )

                messages.success(
                    request, f"Order #{order.id} has been successfully canceled."
                )
        return redirect("orders:order-detail", pk=order.pk)


# Handles creating new orders
class OrderCreateView(LoginRequiredMixin, generic.CreateView):
    model = Order
    template_name = "orders/order_create.html"
    fields = ["client"]

    def get_initial(self):
        # Sets the initial client value if a client_number is provided
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
        # Adds available products and discount options to the context
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.all().order_by("price")

        context["discount_choices"] = [
            (key, f"{value * 100:.0f}%")
            for key, value in self.model.DISCOUNT_CHOICES.items()
        ]
        return context

    def form_valid(self, form):
        # Validates and creates the order and its associated products
        selected_product_ids = self.request.POST.getlist("product")
        discount = self.request.POST.get("discount", "0")
        discount = self.model.DISCOUNT_CHOICES.get(discount, Decimal("0.00"))

        selected_products = []
        for product_id in selected_product_ids:
            quantity_field = f"quantity_{product_id}"
            quantity = int(self.request.POST.get(quantity_field, 0))
            if quantity > 0:
                selected_products.append((product_id, quantity))

        if not selected_products:
            messages.error(
                self.request,
                "Please select at least one product and specify a valid quantity.",
            )
            return render(
                self.request, self.template_name, self.get_context_data(form=form)
            )

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

        order = form.save(commit=False)
        order.agent = self.request.user.agent
        order.discount = discount * 100
        order.status = "Pending"
        order.save()

        for product_id, quantity in selected_products:
            product = get_object_or_404(Product, pk=product_id)
            product.stock_quantity -= quantity
            product.save()

            OrderProduct.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                product_name=product.name,
                product_price=None,
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


# Handles displaying a summary of an order and managing actions like sending offers or canceling the order
class OrderSummaryView(LoginRequiredMixin, generic.DetailView):
    model = Order
    template_name = "orders/order_summary.html"

    def post(self, request, *args, **kwargs):
        # Handles POST actions for sending offers or canceling orders
        order = self.get_object()
        action = request.POST.get("action")

        if action == "send_offer":
            # Generate a unique token for the order offer
            token = str(uuid.uuid4())
            order.offer_token = token
            order.save()

            # Send an email to the client with the offer link
            subject = f"Offer for Order #{order.id}"
            message = f"""
                Dear Client,

                An offer has been made for your order #{order.id}. To review and either accept or deny the offer, please click the link below:

                {self.get_order_confirmation_url(order, token)}

                If you have any questions, please contact us.

                Best regards,
                Dominik Jaroszuk CRM
            """
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,  # Replace with a valid email address
                [order.client.email],
                fail_silently=False,
            )

            # Inform the user and redirect back to the order list
            messages.success(request, "The offer has been sent to the client.")
            return redirect("orders:order-list")

        elif action == "cancel":
            # Restore product quantities and delete the order
            for order_product in order.order_products.all():
                product = order_product.product
                if product:
                    product.stock_quantity += order_product.quantity
                    product.save()

            order.delete()
            messages.success(
                request,
                "The order has been canceled, and product quantities have been restored.",
            )
            return redirect("orders:order-list")

        # Handle invalid actions
        messages.error(request, "Invalid action.")
        return redirect("orders:order-summary", pk=order.pk)

    def get_order_confirmation_url(self, order, token):
        # Generate the confirmation link for the client to accept or deny the order
        domain = get_current_site(self.request).domain
        path = reverse("orders:order_confirm", kwargs={"order_id": order.id})
        query = urlencode({"token": token})
        return f"http://{domain}{path}?{query}"


# Handles client interactions for confirming or denying an order offer
class OrderConfirmView(generic.View):
    def get(self, request, *args, **kwargs):
        # Display the confirmation page for an order offer
        order_id = kwargs["order_id"]
        token = request.GET.get("token")

        # Verify the token matches the one stored in the order
        order = get_object_or_404(Order, pk=order_id)
        if order.offer_token != token:
            messages.error(request, "Invalid or expired offer link.")
            return redirect("orders:order-list")

        return render(request, "orders/order_confirm.html", {"order": order})

    def post(self, request, *args, **kwargs):
        # Handles accepting or denying an order offer
        order_id = kwargs["order_id"]
        token = request.POST.get("token")
        action = request.POST.get("action")

        order = get_object_or_404(Order, pk=order_id)

        # Validate the token
        if order.offer_token != token:
            messages.error(request, "Invalid or expired offer link.")
            return redirect("orders:order-list")

        if action == "accept":
            # Accept the order and send a payment email
            order.status = "Accepted"
            order.save()
            self.send_payment_email(order)

            messages.success(
                request, "The offer has been accepted. A payment email has been sent."
            )
        elif action == "deny":
            # Deny the order and restore product quantities
            order.status = "Canceled"
            order.save()
            for order_product in order.order_products.all():
                product = order_product.product
                if product:
                    product.stock_quantity += order_product.quantity
                    product.save()

            messages.success(
                request, "The offer has been denied, and the order has been canceled."
            )
        else:
            messages.error(request, "Invalid action.")

        return redirect("/")

    def send_payment_email(self, order):
        # Send an email with payment details for the order
        subject = f"Payment Details for Order #{order.id}"
        account_number = "0000 0000 0000 0000"
        client_number = order.client.client_number
        total_price = order.total_price

        message = f"""
        Dear Client,

        Thank you for accepting the offer for your order #{order.id}.

        Please make a payment to the following account number:
        Account Number: {account_number}

        In the payment title, please write: {client_number}, order #{order.id}

        Total Amount: {total_price} USD

        Thank you for your business.

        Best regards,
        Dominik Jaroszuk CRM
        """

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,  # Replace with a valid email address
            [order.client.email],
            fail_silently=False,
        )


# Displays statistics for orders, including revenue, products sold, and completion rates
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

        # Find the biggest and smallest orders using the total_price property
        orders = Order.objects.filter(
            date_created__gte=start_date, date_created__lt=end_date
        )
        biggest_order = max(orders, key=lambda order: order.total_price, default=None)
        smallest_order = min(orders, key=lambda order: order.total_price, default=None)

        # Get daily revenue for the selected month
        orders_by_day = (
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
            for entry in orders_by_day
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
            "biggest_order": biggest_order,
            "smallest_order": smallest_order,
        }
        context["daily_revenue"] = json.dumps(daily_revenue)

        return context
