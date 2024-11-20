# clients/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import get_object_or_404
from .models import Client
from .forms import ClientForm


class ClientListView(LoginRequiredMixin, generic.ListView):
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"

    def get_queryset(self):
        """Zwraca listę wszystkich klientów dla zalogowanych użytkowników."""
        return Client.objects.all()


class ClientDetailView(LoginRequiredMixin, generic.DetailView):
    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"

    def get_object(self):
        """Fetch the client using client_number instead of pk."""
        client_number = self.kwargs["client_number"]
        return get_object_or_404(Client, client_number=client_number)


class ClientCreateView(LoginRequiredMixin, generic.CreateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_create.html"

    def form_valid(self, form):
        """Ustawia organizację i agenta jako domyślną dla użytkownika logującego się."""
        # Set the organisation of the client to the organisation of the logged-in user's profile
        form.instance.organisation = self.request.user.userprofile.organisation

        # Set the agent of the client to the logged-in user’s agent (assuming the agent is linked to the user)
        form.instance.agent = self.request.user.agent

        # Call the parent class's form_valid method to complete the form saving process
        return super().form_valid(form)


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
