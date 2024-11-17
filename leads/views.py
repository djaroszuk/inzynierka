from django.core.mail import send_mail
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import generic
from agents.mixins import OrganisorAndLoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Lead, Category
from .forms import (
    LeadForm,
    CustomUserCreationForm,
    AssignAgentForm,
    LeadCategoryUpdateForm,
)
from django.shortcuts import render, reverse, get_object_or_404
from clients.models import Client


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse("login")


class LeadCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_create.html"
    success_url = reverse_lazy(
        "leads:lead-list"
    )  # Po utworzeniu przekierowuje do listy leadów

    def form_valid(self, form):
        lead = form.save(commit=False)
        lead.organisation = self.request.user.userprofile
        lead.save()
        send_mail(
            subject="A lead has been created",
            message="Go to the site to see the new lead",
            from_email="test@test.com",
            recipient_list=["test2@test.com"],
        )
        messages.success(self.request, "You have successfully created a lead")
        return super(LeadCreateView, self).form_valid(form)


class LeadListView(LoginRequiredMixin, generic.ListView):
    model = Lead
    template_name = "leads/lead-list.html"
    context_object_name = "leads"  # domyślna nazwa dla kontekstu

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(
                organisation=user.userprofile, agent__isnull=False
            )
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            queryset = queryset.filter(agent__user=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(
                organisation=user.userprofile, agent__isnull=True
            )
            context.update({"unassigned_leads": queryset})
        return context


class LeadDetailView(LoginRequiredMixin, generic.DetailView):
    model = Lead
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            queryset = queryset.filter(agent__user=user)
        return queryset


class LeadUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_update.html"
    success_url = reverse_lazy(
        "leads:lead-list"
    )  # Po aktualizacji przekierowuje do listy leadów

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            queryset = queryset.filter(agent__user=user)
        return queryset


class LeadDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Lead
    template_name = "leads/lead_delete.html"
    success_url = reverse_lazy(
        "leads:lead-list"
    )  # Po usunięciu przekierowuje do listy leadów

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            queryset = queryset.filter(agent__user=user)
        return queryset


class LandingPageView(generic.TemplateView):
    template_name = "landing.html"


def landing_page(request):
    return render(request, "landing.html")


class AssignAgentView(OrganisorAndLoginRequiredMixin, generic.FormView):
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignAgentView, self).get_form_kwargs(**kwargs)
        kwargs.update({"request": self.request})
        return kwargs

    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        lead.agent = agent
        lead.save()
        return super(AssignAgentView, self).form_valid(form)


class CategoryListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/category_list.html"
    context_object_name = "category_list"

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        user = self.request.user

        if user.is_organisor:
            queryset = Lead.objects.filter(
                organisation=user.userprofile,
            )
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)

        context.update(
            {"unassigned_lead_count": queryset.filter(category__isnull=True).count()}
        )
        return context

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile,
            )
        else:
            queryset = Category.objects.filter(organisation=user.agent.organisation)
        return queryset


class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super(CategoryDetailView, self).get_context_data(**kwargs)
        leads = self.get_object().leads.all()
        context.update({"leads": leads})
        return context

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile,
            )
        else:
            queryset = Category.objects.filter(organisation=user.agent.organisation)
        return queryset


class LeadCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):

    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            queryset = queryset.filter(agent__user=user)
        return queryset

    def get_success_url(self):
        return reverse("leads:lead-detail", kwargs={"pk": self.get_object().id})


class LeadListByClientView(LoginRequiredMixin, generic.ListView):
    model = Lead
    template_name = "leads/lead_list_by_client.html"
    context_object_name = "leads"

    def get_queryset(self):
        # Get the client ID from the URL
        client_id = self.kwargs.get("client_id")

        # Fetch the client object or return a 404 if not found
        client = get_object_or_404(Client, id=client_id)

        # Filter leads based on the associated client
        return Lead.objects.filter(client=client)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch the client for the context so we can display its details
        client_id = self.kwargs.get("client_id")
        client = get_object_or_404(Client, id=client_id)
        context["client"] = client

        return context
