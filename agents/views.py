# Standard Library Imports
from decimal import Decimal
import json
import random

# Django Core Imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import reverse, get_object_or_404
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views import generic
from django.conf import settings


# Models
from leads.models import Agent
from clients.models import Client, Contact

# Forms
from orders.forms import StatisticsFilterForm
from .forms import AgentModelForm, AgentSearchForm, OrganisorEmailForm, AgentEmailForm

# Custom Mixins
from .mixins import OrganisorAndLoginRequiredMixin


# Agent list with filters and search functionality
class AgentListView(OrganisorAndLoginRequiredMixin, generic.ListView):
    template_name = "agents/agent_list.html"
    context_object_name = "agents"
    paginate_by = 15

    def get_queryset(self):
        queryset = Agent.objects.all()
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                user__username__icontains=query
            )  # Case-insensitive search
        return queryset.order_by("user__username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get paginated queryset
        agents = self.get_queryset()
        paginator = Paginator(agents, self.paginate_by)
        page = self.request.GET.get("page", 1)
        try:
            paginated_agents = paginator.page(page)
        except PageNotAnInteger:
            paginated_agents = paginator.page(1)
        except EmptyPage:
            paginated_agents = paginator.page(paginator.num_pages)
        context["agents"] = paginated_agents  # Add paginated agents to context
        context["form"] = AgentSearchForm(self.request.GET)  # Pre-fill with query data
        return context


# Create a new agent and send them login details
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
            subject="Account Created in Dominik Jaroszuk CRM",
            message=(
                "Your account has been successfully created.\n\n"
                "Thank you for joining our company!\n\n"
                "To log in, please reset your password using the 'Forgot Password' form available on the login page.\n\n"
                "Best regards,\n"
                "Your Company Name"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return super().form_valid(form)


# Display details of a specific agent
class AgentDetailView(OrganisorAndLoginRequiredMixin, generic.DetailView):
    template_name = "agents/agent_detail.html"
    context_object_name = "agent"

    def get_queryset(self):
        return Agent.objects.all()


# Update an agent's details
class AgentUpdateView(OrganisorAndLoginRequiredMixin, generic.UpdateView):
    template_name = "agents/agent_update.html"
    form_class = AgentModelForm

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_queryset(self):
        return Agent.objects.select_related("user")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        agent = self.get_object()
        kwargs["instance"] = agent.user
        return kwargs


# Delete an agent
class AgentDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "agents/agent_delete.html"
    context_object_name = "agent"

    def get_queryset(self):
        return Agent.objects.all()

    def get_success_url(self):
        return reverse("agents:agent-list")


# Display detailed statistics for an agent
class AgentStatsView(OrganisorAndLoginRequiredMixin, generic.DetailView):
    model = Agent
    template_name = "agents/agent_stats.html"
    context_object_name = "agent"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent = self.object

        # Filter form for date range
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        start_datetime = None
        end_datetime = None

        if form.is_valid():
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")

        # Agent statistics
        stats = agent.get_stats(start_datetime, end_datetime)
        context["stats"] = stats

        # Calculate lead conversion rate
        total_leads = stats.get("sale", 0) + stats.get("no_sale", 0)
        conversion_rate = (
            (stats.get("sale", 0) / total_leads * 100) if total_leads > 0 else None
        )
        context["conversion_rate"] = conversion_rate

        # Daily and monthly data
        daily_orders_data = agent.get_daily_order_data(days=30)
        monthly_revenue_data = agent.get_monthly_revenue_data(months=12)

        context["daily_orders_data_json"] = json.dumps(daily_orders_data)
        context["monthly_revenue_data_json"] = json.dumps(monthly_revenue_data)

        return context


# Display aggregated statistics for all agents
class AllAgentsStatsView(OrganisorAndLoginRequiredMixin, generic.TemplateView):
    template_name = "agents/all_agents_stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filter form for optional date filtering
        form = StatisticsFilterForm(self.request.GET or None)
        context["form"] = form

        start_datetime = None
        end_datetime = None
        if form.is_valid():
            start_datetime = form.cleaned_data.get("start_datetime")
            end_datetime = form.cleaned_data.get("end_datetime")

        agents = Agent.objects.all()

        total_orders = 0
        total_value = Decimal("0.0")
        total_sales = 0
        total_no_sales = 0

        daily_orders_map = {}
        monthly_revenue_map = {}

        # Aggregate stats from all agents
        for agent in agents:
            stats = agent.get_stats(start_datetime, end_datetime)

            # Accumulate stats
            total_orders += stats["order_count"]
            total_value += stats["total_value"]
            total_sales += stats["sale"]
            total_no_sales += stats["no_sale"]

            # Aggregate daily orders
            daily_data = agent.get_daily_order_data(days=30)
            for entry in daily_data:
                date = entry["date"]
                daily_orders_map[date] = daily_orders_map.get(date, 0) + entry["count"]

            # Aggregate monthly revenue
            monthly_data = agent.get_monthly_revenue_data(months=12)
            for entry in monthly_data:
                month = entry["month"]
                monthly_revenue_map[month] = (
                    monthly_revenue_map.get(month, 0) + entry["revenue"]
                )

        # Compute overall conversion rate
        total_leads = total_sales + total_no_sales
        overall_conversion_rate = (
            (total_sales / total_leads * 100) if total_leads > 0 else None
        )

        # Compute averages for charts
        agent_count = agents.count()
        average_daily_orders = [
            {"date": d, "average_count": c / agent_count if agent_count > 0 else 0}
            for d, c in daily_orders_map.items()
        ]
        average_monthly_revenue = [
            {"month": m, "average_revenue": r / agent_count if agent_count > 0 else 0}
            for m, r in monthly_revenue_map.items()
        ]

        # Pass aggregated stats and chart data to context
        context["stats"] = {
            "order_count": total_orders,
            "total_value": total_value,
            "average_order_value": (
                total_value / total_orders if total_orders > 0 else 0
            ),
            "sale": total_sales,
            "no_sale": total_no_sales,
            "conversion_rate": overall_conversion_rate,
        }

        context["daily_orders_data_json"] = json.dumps(average_daily_orders)
        context["monthly_revenue_data_json"] = json.dumps(average_monthly_revenue)

        return context


# Send an email to a specific client or all clients
class SendEmailView(LoginRequiredMixin, generic.FormView):
    template_name = "agents/send_email.html"
    form_class = None
    success_url = reverse_lazy("agents:send-email")

    def get_initial(self):
        # Prefill with client data if passed
        initial = super().get_initial()
        client_number = self.request.GET.get("client_number")
        if client_number:
            initial["client_number"] = client_number
        return initial

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["is_organisor"] = self.request.user.is_organisor

        # Include prefilled client number in the context
        client_number = self.request.GET.get("client_number")
        if client_number:
            context["prefilled_client_number"] = client_number
        else:
            context["prefilled_client_number"] = None

        return context

    def get_form_class(self):
        # Returns a form class dynamically based on user role
        if self.request.user.is_organisor:
            return OrganisorEmailForm
        return AgentEmailForm

    def form_valid(self, form):
        # Sending emails form validation

        send_to_all = form.cleaned_data.get("send_to_all", False)
        client_number = form.cleaned_data.get("client_number")

        subject = form.cleaned_data["subject"]
        message = form.cleaned_data["message"]

        if send_to_all:
            if self.request.user.is_organisor:
                # Retrieve all clients
                clients = Client.objects.all()

                if not clients:
                    form.add_error(None, "No clients available to send emails.")
                    return self.form_invalid(form)

                recipient_list = [client.email for client in clients if client.email]

                if recipient_list:
                    send_mail(
                        subject,
                        message,
                        self.request.user.email,  # From email
                        recipient_list,  # To emails
                    )
                    messages.success(
                        self.request,
                        f"Email sent successfully to {len(recipient_list)} clients.",
                    )

                    # Create contact entries for all clients
                    for client in clients:
                        Contact.objects.create(
                            client=client,
                            reason=Contact.ReasonChoices.OTHER,
                            description=f"An email with subject '{subject}' was sent to the client.",
                            contact_date=now(),
                            user=self.request.user.userprofile,
                        )
                else:
                    form.add_error(None, "No valid client emails available.")
                    messages.error(
                        self.request,
                        "You do not have permission to send emails to all clients.",
                    )
                    return self.form_invalid(form)
            else:
                form.add_error(
                    None, "You do not have permission to send emails to all clients."
                )
                return self.form_invalid(form)
        else:
            if not client_number:
                form.add_error(
                    "client_number", "Client Number is required to send an email."
                )
                return self.form_invalid(form)

            client = get_object_or_404(Client, client_number=client_number)

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,  # From email
                [client.email],  # To email
            )
            messages.success(
                self.request, f"Email sent successfully to {client.email}."
            )

            # Create a contact entry for the specific client
            Contact.objects.create(
                client=client,
                reason=Contact.ReasonChoices.OTHER,
                description=f"An email with subject '{subject}' was sent to the client.",
                contact_date=now(),
                user=self.request.user.userprofile,
            )

        return super().form_valid(form)
