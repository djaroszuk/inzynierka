# Standard Library Imports
from datetime import timedelta
import json

# Django Core Imports
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

# Custom Mixins
from agents.mixins import OrganisorAndLoginRequiredMixin

# Forms
from orders.forms import StatisticsFilterForm
from .forms import ClientForm, ClientSearchForm, ContactForm, OrganisorClientForm

# Models
from .models import Client, Contact


# Displays a list of clients with search and filter functionality
class ClientListView(LoginRequiredMixin, generic.ListView):
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"
    paginate_by = 10

    def get_queryset(self):
        # Returns a list of clients filtered by search and criteria
        queryset = Client.objects.all()

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(Q(client_number__icontains=query))

        if self.request.GET.get("important"):
            queryset = queryset.filter(status="Important")

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
                pass

        return queryset.order_by("-converted_date")

    def get_context_data(self, **kwargs):
        # Adds the search form and pagination to the context
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
        context["form"] = ClientSearchForm(self.request.GET)
        return context


# Displays detailed information about a specific client
class ClientDetailView(LoginRequiredMixin, generic.DetailView):
    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"

    def get_object(self):
        # Fetches the client using client_number
        client_number = self.kwargs["client_number"]
        return get_object_or_404(Client, client_number=client_number)


# Allows updating of client details with role-based forms
class ClientUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Client
    form_class = None
    template_name = "clients/client_update.html"
    success_url = reverse_lazy("clients:client-list")

    def get_object(self):
        # Fetches the client using client_number
        client_number = self.kwargs["client_number"]
        return get_object_or_404(Client, client_number=client_number)

    def get_form_class(self):
        # Returns a form class dynamically based on user role
        if self.request.user.is_organisor:
            return OrganisorClientForm
        return ClientForm


# Handles client deletion with permission checks
class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Client
    template_name = "clients/client_delete.html"
    success_url = reverse_lazy("clients:client-list")

    def test_func(self):
        # Checks if the user is an organisor
        return self.request.user.is_organisor

    def get_object(self):
        # Fetches the client using client_number
        client_number = self.kwargs["client_number"]
        return get_object_or_404(Client, client_number=client_number)


# Displays a list of contacts for a specific client
class ContactListView(LoginRequiredMixin, generic.ListView):
    model = Contact
    template_name = "clients/contact_list.html"
    context_object_name = "contacts"

    def get_queryset(self):
        # Filters contacts for a specific client
        client_number = self.kwargs.get("client_number")
        client = get_object_or_404(Client, client_number=client_number)
        return Contact.objects.filter(client=client).order_by("-contact_date")

    def get_context_data(self, **kwargs):
        # Adds the client to the context
        context = super().get_context_data(**kwargs)
        client_number = self.kwargs.get("client_number")
        context["client"] = get_object_or_404(Client, client_number=client_number)
        return context


# Allows creation of a new contact for a specific client
class ContactCreateView(LoginRequiredMixin, generic.CreateView):
    model = Contact
    template_name = "clients/contact_form.html"
    form_class = ContactForm

    def get_context_data(self, **kwargs):
        # Adds the client to the context
        context = super().get_context_data(**kwargs)
        client_number = self.kwargs.get("client_number")
        context["client"] = get_object_or_404(Client, client_number=client_number)
        return context

    def form_valid(self, form):
        # Assigns the client and logged-in user before saving
        client_number = self.kwargs.get("client_number")
        client = get_object_or_404(Client, client_number=client_number)
        form.instance.client = client
        user_profile = self.request.user.userprofile
        form.instance.user = user_profile
        return super().form_valid(form)

    def get_success_url(self):
        # Redirects to the contact list after creating a contact
        client_number = self.kwargs.get("client_number")
        return reverse_lazy(
            "clients:contact-list", kwargs={"client_number": client_number}
        )


# Displays statistics for a specific client
class ClientStatisticsView(LoginRequiredMixin, generic.TemplateView):
    template_name = "clients/client_statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        start_datetime = None
        end_datetime = None

        if form.is_valid():
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")

        client_number = self.kwargs.get("client_number")
        client = get_object_or_404(Client, client_number=client_number)

        client_statistics = client.order_statistics(
            start_date=start_datetime, end_date=end_datetime
        )

        monthly_order_stats = client.monthly_order_stats(
            start_date=start_datetime, end_date=end_datetime
        )

        monthly_aov = client.monthly_average_order_value(
            start_date=start_datetime, end_date=end_datetime
        )

        monthly_order_stats_json = json.dumps(
            monthly_order_stats, cls=DjangoJSONEncoder
        )
        monthly_aov_json = json.dumps(monthly_aov, cls=DjangoJSONEncoder)

        context["client"] = client
        context["client_statistics"] = client_statistics
        context["monthly_order_stats"] = monthly_order_stats_json
        context["monthly_aov"] = monthly_aov_json

        return context


# Displays aggregate statistics for all clients
class AllClientsStatisticsView(OrganisorAndLoginRequiredMixin, generic.TemplateView):
    template_name = "clients/all_clients_statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        start_datetime = None
        end_datetime = None

        if form.is_valid():
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")

        clients = Client.objects.all()
        total_clients = clients.count()
        baseline_value = 500
        all_clients_statistics = {
            "total_revenue": 0,
            "total_products_sold": 0,
            "total_orders": 0,
        }
        monthly_order_stats = []
        monthly_aov = []
        ltv_data = {"labels": [], "ltv_values": []}
        unique_clients_with_orders = set()

        cumulative_revenue_by_period = {}

        client_statistics = []
        for client in clients:
            stats = client.order_statistics(
                start_date=start_datetime, end_date=end_datetime
            )
            all_clients_statistics["total_revenue"] += stats["total_revenue"]
            all_clients_statistics["total_products_sold"] += stats[
                "total_products_sold"
            ]
            all_clients_statistics["total_orders"] += stats["total_orders"]

            if stats["total_orders"] > 0:
                unique_clients_with_orders.add(client.pk)

                client_statistics.append(
                    {
                        "client": client,
                        "total_revenue": stats["total_revenue"],
                        "total_orders": stats["total_orders"],
                    }
                )

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

            client_ltv = client.lifetime_value_over_time()
            for label, value in zip(client_ltv["labels"], client_ltv["ltv_values"]):
                if label not in cumulative_revenue_by_period:
                    cumulative_revenue_by_period[label] = 0
                cumulative_revenue_by_period[label] += value

        best_clients = sorted(
            client_statistics, key=lambda x: x["total_revenue"], reverse=True
        )[:3]

        best_clients_data = [
            {
                "number": client_data["client"].client_number,
                "total_revenue": client_data["total_revenue"],
                "total_orders": client_data["total_orders"],
            }
            for client_data in best_clients
        ]

        sorted_labels = sorted(cumulative_revenue_by_period.keys())

        for label in sorted_labels:
            total_revenue = cumulative_revenue_by_period[label]
            avg_ltv = total_revenue / total_clients if total_clients > 0 else 0
            ltv_data["labels"].append(label)
            ltv_data["ltv_values"].append(round(avg_ltv, 2))

        consolidated_monthly_stats = self.consolidate_monthly_data(monthly_order_stats)
        consolidated_monthly_aov = self.consolidate_monthly_aov(monthly_aov)

        consolidated_monthly_stats_json = json.dumps(
            consolidated_monthly_stats, cls=DjangoJSONEncoder
        )
        consolidated_monthly_aov_json = json.dumps(
            consolidated_monthly_aov, cls=DjangoJSONEncoder
        )
        ltv_data_json = json.dumps(ltv_data, cls=DjangoJSONEncoder)

        context["all_clients_statistics"] = all_clients_statistics
        context["monthly_order_stats"] = consolidated_monthly_stats_json
        context["monthly_aov"] = consolidated_monthly_aov_json
        context["ltv_data"] = ltv_data_json
        context["baseline_value"] = baseline_value
        context["total_clients"] = len(unique_clients_with_orders)
        context["best_clients"] = best_clients_data

        return context

    def consolidate_monthly_data(self, monthly_order_stats):
        # Consolidates monthly order stats for all clients
        consolidated = {}
        for stats in monthly_order_stats:
            for label, orders, spent in zip(
                stats["labels"], stats["order_counts"], stats["total_spent"]
            ):
                if label not in consolidated:
                    consolidated[label] = {"order_counts": 0, "total_spent": 0}
                consolidated[label]["order_counts"] += orders
                consolidated[label]["total_spent"] += spent

        labels = sorted(consolidated.keys())
        return {
            "labels": labels,
            "order_counts": [consolidated[label]["order_counts"] for label in labels],
            "total_spent": [consolidated[label]["total_spent"] for label in labels],
        }

    def consolidate_monthly_aov(self, monthly_aov):
        # Consolidates monthly Average Order Value (AOV) for all clients
        consolidated = {}
        for stats in monthly_aov:
            for label, aov in zip(stats["labels"], stats["average_order_value"]):
                if label not in consolidated:
                    consolidated[label] = {"total_aov": 0, "count": 0}
                consolidated[label]["total_aov"] += aov
                consolidated[label]["count"] += 1

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
