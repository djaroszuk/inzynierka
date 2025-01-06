# clients/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import get_object_or_404
from .models import Client, Contact
from .forms import ClientForm, ContactForm, ClientSearchForm
from django.db.models import Q
from orders.forms import StatisticsFilterForm
from datetime import timedelta
from django.utils import timezone
import json
from django.core.serializers.json import DjangoJSONEncoder


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class ClientListView(LoginRequiredMixin, generic.ListView):
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"
    paginate_by = 2  # Number of items per page

    def get_queryset(self):
        """Return a list of clients filtered by the search query."""
        queryset = Client.objects.all()

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(client_number__icontains=query)  # Case-insensitive search
            )

        # Filter by Important Clients (checkbox)
        if self.request.GET.get("important"):
            queryset = queryset.filter(
                status="Important"
            )  # Assuming `status` is used to mark clients as important

        # Filter by Last Sales Offer Contact (days ago)
        last_contacted_days = self.request.GET.get("last_contacted")
        if last_contacted_days:
            try:
                days = int(last_contacted_days)
                cutoff_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(
                    contacts__reason=Contact.ReasonChoices.SALES_OFFER,
                    contacts__contact_date__lte=cutoff_date,
                ).distinct()
            except ValueError:
                # If the value is not a valid integer, just ignore the filter
                pass

        return queryset

    def get_context_data(self, **kwargs):
        """Add the search form and pagination to the context."""
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get("page")

        try:
            clients = paginator.page(page)
        except PageNotAnInteger:
            clients = paginator.page(1)
        except EmptyPage:
            clients = paginator.page(paginator.num_pages)

        context["clients"] = clients
        context["form"] = ClientSearchForm(self.request.GET)  # Pre-fill with query data
        return context


class ClientDetailView(LoginRequiredMixin, generic.DetailView):
    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"

    def get_object(self):
        """Fetch the client using client_number instead of pk."""
        client_number = self.kwargs["client_number"]
        return get_object_or_404(Client, client_number=client_number)


class ClientUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_update.html"
    success_url = reverse_lazy(
        "clients:client-list"
    )  # Po aktualizacji przekierowuje do listy leadów

    def get_object(self):
        """Fetch the client using client_number instead of pk."""
        client_number = self.kwargs["client_number"]
        return get_object_or_404(Client, client_number=client_number)


class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Client
    template_name = "clients/client_delete.html"
    success_url = reverse_lazy("clients:client-list")

    def test_func(self):
        """Sprawdza, czy użytkownik jest organizatorem."""
        return self.request.user.is_organisor

    def get_object(self):
        """Fetch the client using client_number instead of pk."""
        client_number = self.kwargs["client_number"]
        return get_object_or_404(Client, client_number=client_number)


class ContactListView(LoginRequiredMixin, generic.ListView):
    model = Contact
    template_name = "clients/contact_list.html"
    context_object_name = "contacts"

    def get_queryset(self):
        """Filter contacts for a specific client using client_number."""
        client_number = self.kwargs.get("client_number")
        client = get_object_or_404(Client, client_number=client_number)
        return Contact.objects.filter(client=client).order_by("-contact_date")

    def get_context_data(self, **kwargs):
        """Add the client to the context using client_number."""
        context = super().get_context_data(**kwargs)
        client_number = self.kwargs.get("client_number")
        context["client"] = get_object_or_404(Client, client_number=client_number)
        return context


class ContactCreateView(LoginRequiredMixin, generic.CreateView):
    model = Contact
    template_name = "clients/contact_form.html"
    form_class = ContactForm

    def get_context_data(self, **kwargs):
        """Add the client to the context using client_number."""
        context = super().get_context_data(**kwargs)
        client_number = self.kwargs.get("client_number")
        context["client"] = get_object_or_404(Client, client_number=client_number)
        return context

    def form_valid(self, form):
        """Assign the client and the logged-in user before saving."""
        client_number = self.kwargs.get("client_number")
        client = get_object_or_404(Client, client_number=client_number)
        form.instance.client = client
        user_profile = self.request.user.userprofile
        form.instance.user = user_profile
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the contact list after creating a contact."""
        client_number = self.kwargs.get("client_number")
        return reverse_lazy(
            "clients:contact-list", kwargs={"client_number": client_number}
        )


class ClientStatisticsView(generic.TemplateView):
    template_name = "clients/client_statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize the filter form with GET data if available
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        # Extract filtering variables
        start_datetime = None
        end_datetime = None

        if form.is_valid():
            # Retrieve validated data from the form
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")

        # Fetch the client based on the client_number from the URL
        client_number = self.kwargs.get("client_number")
        client = get_object_or_404(Client, client_number=client_number)

        # Fetch client statistics
        client_statistics = client.order_statistics(
            start_date=start_datetime, end_date=end_datetime
        )

        # Fetch monthly order stats using the model method
        monthly_order_stats = client.monthly_order_stats(
            start_date=start_datetime, end_date=end_datetime
        )

        # Fetch monthly average order value using the new model method
        monthly_aov = client.monthly_average_order_value(
            start_date=start_datetime, end_date=end_datetime
        )

        # Convert the data to JSON using DjangoJSONEncoder
        monthly_order_stats_json = json.dumps(
            monthly_order_stats, cls=DjangoJSONEncoder
        )
        monthly_aov_json = json.dumps(monthly_aov, cls=DjangoJSONEncoder)

        # Add to context
        context["client"] = client
        context["client_statistics"] = client_statistics
        context["monthly_order_stats"] = monthly_order_stats_json
        context["monthly_aov"] = monthly_aov_json  # New context variable

        return context


class AllClientsStatisticsView(generic.TemplateView):
    template_name = "clients/all_clients_statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize the filter form with GET data if available
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        # Extract filtering variables
        start_datetime = None
        end_datetime = None
        group_by = self.request.GET.get(
            "group_by", "month"
        )  # Default grouping: monthly

        if form.is_valid():
            # Retrieve validated data from the form
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")

        # Fetch all clients
        clients = Client.objects.all()
        total_clients = clients.count()
        baseline_value = 500  # Baseline for LTV
        all_clients_statistics = {
            "total_revenue": 0,
            "total_products_sold": 0,
            "total_orders": 0,
        }
        monthly_order_stats = []
        monthly_aov = []
        ltv_data = {"labels": [], "ltv_values": []}

        # Prepare cumulative LTV
        cumulative_revenue_by_period = {}

        for client in clients:
            # Gather overall statistics
            stats = client.order_statistics(
                start_date=start_datetime, end_date=end_datetime
            )
            all_clients_statistics["total_revenue"] += stats["total_revenue"]
            all_clients_statistics["total_products_sold"] += stats[
                "total_products_sold"
            ]
            all_clients_statistics["total_orders"] += stats["total_orders"]

            # Append monthly data for charts
            monthly_order_stats.append(
                client.monthly_order_stats(
                    start_date=start_datetime, end_date=end_datetime
                )
            )
            monthly_aov.append(
                client.monthly_average_order_value(
                    start_date=start_datetime, end_date=end_datetime
                )
            )

            # Fetch cumulative LTV for the client
            client_ltv = client.lifetime_value_over_time(group_by=group_by)
            for label, value in zip(client_ltv["labels"], client_ltv["ltv_values"]):
                if label not in cumulative_revenue_by_period:
                    cumulative_revenue_by_period[label] = 0
                cumulative_revenue_by_period[label] += value

        # Sort labels (time periods) for consistent chart display
        sorted_labels = sorted(cumulative_revenue_by_period.keys())

        # Calculate average LTV across all clients
        for label in sorted_labels:
            total_revenue = cumulative_revenue_by_period[label]
            avg_ltv = total_revenue / total_clients if total_clients > 0 else 0
            ltv_data["labels"].append(label)
            ltv_data["ltv_values"].append(round(avg_ltv, 2))

        # Consolidate monthly data for all clients
        consolidated_monthly_stats = self.consolidate_monthly_data(monthly_order_stats)
        consolidated_monthly_aov = self.consolidate_monthly_aov(monthly_aov)

        # Convert data to JSON using DjangoJSONEncoder
        consolidated_monthly_stats_json = json.dumps(
            consolidated_monthly_stats, cls=DjangoJSONEncoder
        )
        consolidated_monthly_aov_json = json.dumps(
            consolidated_monthly_aov, cls=DjangoJSONEncoder
        )
        ltv_data_json = json.dumps(ltv_data, cls=DjangoJSONEncoder)

        # Add data to context
        context["all_clients_statistics"] = all_clients_statistics
        context["monthly_order_stats"] = consolidated_monthly_stats_json
        context["monthly_aov"] = consolidated_monthly_aov_json
        context["ltv_data"] = ltv_data_json
        context["baseline_value"] = baseline_value
        context["total_clients"] = total_clients

        return context

    def consolidate_monthly_data(self, monthly_order_stats):
        """
        Consolidates monthly order stats for all clients.
        """
        consolidated = {}
        for stats in monthly_order_stats:
            for label, orders, spent in zip(
                stats["labels"], stats["order_counts"], stats["total_spent"]
            ):
                if label not in consolidated:
                    consolidated[label] = {"order_counts": 0, "total_spent": 0}
                consolidated[label]["order_counts"] += orders
                consolidated[label]["total_spent"] += spent

        # Convert to sorted list for chart.js
        labels = sorted(consolidated.keys())
        return {
            "labels": labels,
            "order_counts": [consolidated[label]["order_counts"] for label in labels],
            "total_spent": [consolidated[label]["total_spent"] for label in labels],
        }

    def consolidate_monthly_aov(self, monthly_aov):
        """
        Consolidates monthly Average Order Value (AOV) for all clients.
        """
        consolidated = {}
        for stats in monthly_aov:
            for label, aov in zip(stats["labels"], stats["average_order_value"]):
                if label not in consolidated:
                    consolidated[label] = {"total_aov": 0, "count": 0}
                consolidated[label]["total_aov"] += aov
                consolidated[label]["count"] += 1

        # Calculate average AOV per month
        labels = sorted(consolidated.keys())
        return {
            "labels": labels,
            "average_order_value": [
                round(
                    consolidated[label]["total_aov"] / consolidated[label]["count"], 2
                )
                for label in labels
            ],
        }
