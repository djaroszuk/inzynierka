# from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from .models import Lead
from .forms import LeadForm


class LeadCreateView(generic.CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_create.html"
    success_url = reverse_lazy(
        "leads:lead-list"
    )  # Po utworzeniu przekierowuje do listy leadów


class LeadListView(generic.ListView):
    model = Lead
    template_name = "leads/lead-list.html"
    context_object_name = "leads"  # domyślna nazwa dla kontekstu


class LeadDetailView(generic.DetailView):
    model = Lead
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"


class LeadUpdateView(generic.UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_update.html"
    success_url = reverse_lazy(
        "leads:lead-list"
    )  # Po aktualizacji przekierowuje do listy leadów


class LeadDeleteView(generic.DeleteView):
    model = Lead
    template_name = "leads/lead_delete.html"
    success_url = reverse_lazy(
        "leads:lead-list"
    )  # Po usunięciu przekierowuje do listy leadów
