from django.core.mail import send_mail
from django.views import generic
import random
from django.shortcuts import reverse
from leads.models import Agent
from .forms import AgentModelForm, EmailForm, AgentSearchForm
from .mixins import OrganisorAndLoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from django.urls import reverse_lazy
from clients.models import Client, Contact
from django.utils.timezone import now
from django.shortcuts import get_object_or_404


from orders.forms import StatisticsFilterForm
from decimal import Decimal


class AgentListView(OrganisorAndLoginRequiredMixin, generic.ListView):
    template_name = "agents/agent_list.html"
    context_object_name = "agents"

    def get_queryset(self):
        """Return a list of agents filtered by the search query."""
        queryset = Agent.objects.all()

        # Filter by username
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                user__username__icontains=query
            )  # Case-insensitive search

        return queryset

    def get_context_data(self, **kwargs):
        """Add the search form to the context."""
        context = super().get_context_data(**kwargs)
        context["form"] = AgentSearchForm(self.request.GET)  # Pre-fill with query data
        return context


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
        # Query the Agent model for the specific agent
        return Agent.objects.select_related(
            "user"
        )  # Use select_related for efficiency with related `user` data

    def get_form_kwargs(self):
        # Pass the `instance` of the associated User to the form
        kwargs = super().get_form_kwargs()
        agent = self.get_object()
        kwargs["instance"] = agent.user  # Ensures the form updates the User model
        return kwargs


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


class SendEmailView(LoginRequiredMixin, generic.FormView):
    template_name = "agents/send_email.html"
    form_class = EmailForm
    success_url = reverse_lazy("agents:send-email")

    def get_initial(self):
        """
        Pre-fill the form with initial data if 'client_number' is provided in the query params.
        """
        initial = super().get_initial()
        client_number = self.request.GET.get("client_number")
        if client_number:
            print(f"[DEBUG] Prefilling form with client_number: {client_number}")
            initial["client_number"] = client_number
        return initial

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        """
        context = super().get_context_data(**kwargs)
        context["is_organisor"] = self.request.user.is_organisor

        # Include prefilled client number in the context
        client_number = self.request.GET.get("client_number")
        if client_number:
            context["prefilled_client_number"] = client_number
        else:
            context["prefilled_client_number"] = None

        return context

    def form_valid(self, form):
        """
        Handle valid form submission for sending emails.
        """
        print("[DEBUG] form_valid called.")  # Debug to confirm method execution

        send_to_all = form.cleaned_data.get("send_to_all", False)
        client_number = form.cleaned_data.get("client_number")

        print(f"[DEBUG] send_to_all: {send_to_all}, client_number: {client_number}")

        subject = form.cleaned_data["subject"]
        message = form.cleaned_data["message"]

        if send_to_all:
            if self.request.user.is_organisor:
                print("[DEBUG] User is an organizer and selected 'Send to All'.")
                # Retrieve all clients
                clients = Client.objects.all()
                print(
                    f"[DEBUG] Retrieved clients: {[client.email for client in clients]}"
                )

                if not clients:
                    print("[WARNING] No clients found.")
                    form.add_error(None, "No clients available to send emails.")
                    return self.form_invalid(form)

                recipient_list = [client.email for client in clients if client.email]
                print(f"[DEBUG] Recipient list: {recipient_list}")

                if recipient_list:
                    send_mail(
                        subject,
                        message,
                        self.request.user.email,  # From email
                        recipient_list,  # To emails
                    )
                    print("[INFO] Emails sent to all clients successfully.")

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
                    print("[WARNING] Recipient list is empty. No emails sent.")
                    form.add_error(None, "No valid client emails available.")
                    return self.form_invalid(form)
            else:
                print("[WARNING] Non-organizer user tried to send to all clients.")
                form.add_error(
                    None, "You do not have permission to send emails to all clients."
                )
                return self.form_invalid(form)
        else:
            print("[DEBUG] Sending to a specific client.")
            if not client_number:
                print("[WARNING] Client number not provided.")
                form.add_error(
                    "client_number", "Client Number is required to send an email."
                )
                return self.form_invalid(form)

            client = get_object_or_404(Client, client_number=client_number)

            send_mail(
                subject,
                message,
                self.request.user.email,  # From email
                [client.email],  # To email
            )
            print(f"[INFO] Email sent to {client.email} successfully.")

            # Create a contact entry for the specific client
            Contact.objects.create(
                client=client,
                reason=Contact.ReasonChoices.OTHER,
                description=f"An email with subject '{subject}' was sent to the client.",
                contact_date=now(),
                user=self.request.user.userprofile,
            )

        return super().form_valid(form)
