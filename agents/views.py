from django.core.mail import send_mail
from django.views import generic
import random
from django.shortcuts import reverse
from leads.models import Agent
from .forms import AgentModelForm
from .mixins import OrganisorAndLoginRequiredMixin
import json

from orders.forms import StatisticsFilterForm
from decimal import Decimal


class AgentListView(OrganisorAndLoginRequiredMixin, generic.ListView):
    template_name = "agents/agent_list.html"
    context_object_name = "agents"

    def get_queryset(self):
        return Agent.objects.all


class AgentCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
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
        Agent.objects.create(user=user)
        send_mail(
            subject="TODO.",
            message="TODO.",
            from_email="admin@test.com",
            recipient_list=[user.email],
        )
        return super(AgentCreateView, self).form_valid(form)


class AgentDetailView(OrganisorAndLoginRequiredMixin, generic.DetailView):
    template_name = "agents/agent_detail.html"
    context_object_name = "agent"

    def get_queryset(self):
        return Agent.objects.all()


class AgentUpdateView(OrganisorAndLoginRequiredMixin, generic.UpdateView):
    template_name = "agents/agent_update.html"
    form_class = AgentModelForm

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_queryset(self):
        return Agent.objects.all()


class AgentDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "agents/agent_delete.html"
    context_object_name = "agent"

    def get_queryset(self):
        return Agent.objects.all()

    def get_success_url(self):
        return reverse("agents:agent-list")


class AgentStatsView(generic.DetailView):
    model = Agent
    template_name = "agents/agent_stats.html"
    context_object_name = "agent"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent = self.object

        # Initialize the filter form with GET data
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        start_datetime = None
        end_datetime = None

        if form.is_valid():
            # If the user provided start/end datetimes, use them
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")

        # Now call get_stats with the filtered dates if provided
        context["stats"] = agent.get_stats(start_datetime, end_datetime)

        # The rest of your daily/monthly data retrieval remains unchanged
        daily_orders_data = agent.get_daily_order_data(days=7)
        monthly_revenue_data = agent.get_monthly_revenue_data(months=6)

        context["daily_orders_data_json"] = json.dumps(daily_orders_data)
        context["monthly_revenue_data_json"] = json.dumps(monthly_revenue_data)

        return context


class AllAgentsStatsView(generic.TemplateView):
    template_name = "agents/all_agents_stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filter form to allow optional date filtering
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        start_datetime = None
        end_datetime = None

        if form.is_valid():
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")

        agents = Agent.objects.all()

        # Initialize accumulators for aggregated stats
        total_orders = 0
        total_value = Decimal("0.0")
        total_sale = 0
        total_no_sale = 0

        # Dictionaries to aggregate daily orders and monthly revenue
        daily_orders_map = {}  # {date: total_count_across_all_agents}
        monthly_revenue_map = {}  # {month: total_revenue_across_all_agents}

        for agent in agents:
            # Get agent-level stats
            stats = agent.get_stats(start_datetime, end_datetime)
            total_orders += stats["order_count"]
            total_value += stats["total_value"]
            total_sale += stats["sale"]
            total_no_sale += stats["no_sale"]

            # Aggregate daily orders
            daily_data = agent.get_daily_order_data(days=7)
            for entry in daily_data:
                date = entry["date"]
                daily_orders_map[date] = daily_orders_map.get(date, 0) + entry["count"]

            # Aggregate monthly revenue
            monthly_data = agent.get_monthly_revenue_data(months=6)
            for entry in monthly_data:
                month = entry["month"]
                monthly_revenue_map[month] = (
                    monthly_revenue_map.get(month, 0) + entry["revenue"]
                )

        # Compute the average order value across all agents' orders
        average_order_value = total_value / total_orders if total_orders > 0 else 0

        # Prepare the aggregated stats dict
        context["stats"] = {
            "order_count": total_orders,
            "total_value": total_value,
            "average_order_value": average_order_value,
            "sale": total_sale,
            "no_sale": total_no_sale,
        }

        # Convert the daily and monthly maps to sorted lists
        daily_orders_data = [
            {"date": d, "count": c} for d, c in daily_orders_map.items()
        ]
        daily_orders_data.sort(key=lambda x: x["date"])

        monthly_revenue_data = [
            {"month": m, "revenue": r} for m, r in monthly_revenue_map.items()
        ]
        monthly_revenue_data.sort(key=lambda x: x["month"])

        context["daily_orders_data_json"] = json.dumps(daily_orders_data)
        context["monthly_revenue_data_json"] = json.dumps(monthly_revenue_data)

        return context
