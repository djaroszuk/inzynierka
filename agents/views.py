from django.core.mail import send_mail
from django.views import generic
import random
from django.shortcuts import reverse
from leads.models import Agent
from .forms import AgentModelForm


class AgentListView(generic.ListView):
    template_name = "agents/agent_list.html"
    context_object_name = "agents"

    def get_queryset(self):
        return Agent.objects.all()


class AgentCreateView(generic.CreateView):
    template_name = "agents/agent_create.html"
    form_class = AgentModelForm

    def get_success_url(self):
        return reverse("agents:agent-list")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_agent = True
        user.is_organisor = False
        user.set_password(f"{random.randint(0, 100000)}")
        user.save()
        Agent.objects.create(user=user, organisation=self.request.user.userprofile)
        send_mail(
            subject="TODO.",
            message="TODO.",
            from_email="admin@test.com",
            recipient_list=[user.email],
        )
        return super(AgentCreateView, self).form_valid(form)


class AgentDetailView(generic.DetailView):
    template_name = "agents/agent_detail.html"
    context_object_name = "agent"

    def get_queryset(self):
        return Agent.objects.all()


class AgentUpdateView(generic.UpdateView):
    template_name = "agents/agent_update.html"
    form_class = AgentModelForm

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_queryset(self):
        return Agent.objects.all()


class AgentDeleteView(generic.DeleteView):
    template_name = "agents/agent_delete.html"
    context_object_name = "agent"

    def get_queryset(self):
        return Agent.objects.all()
        return reverse("agents:agent-list")
