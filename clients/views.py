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


class ClientListView(LoginRequiredMixin, generic.ListView):
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"

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
        """Add the search form to the context."""
        context = super().get_context_data(**kwargs)
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

        # Fetch client statistics using the methods defined in the Client model
        client_statistics = client.order_statistics(
            start_date=start_datetime, end_date=end_datetime
        )

        # Add the client and statistics to the context
        context["client"] = client
        context["client_statistics"] = client_statistics

        return context
