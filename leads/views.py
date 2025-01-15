import openpyxl
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, reverse, redirect
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.utils.timezone import now
from django.views import generic, View
from agents.mixins import OrganisorAndLoginRequiredMixin
from .models import Lead, Category
from clients.models import Client
from .forms import (
    LeadForm,
    CustomUserCreationForm,
    LeadCategoryUpdateForm,
    CategoryFilterForm,
    LeadUploadForm,
    LeadAgentForm,
)


# View for signing up new users (registration).
class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse("login")


# View to display a list of leads with pagination and filtering.
class LeadListView(LoginRequiredMixin, generic.ListView):
    model = Lead
    template_name = "leads/lead-list.html"
    context_object_name = "leads"
    paginate_by = 9  # Pagination set to 9 leads per page

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            return self.post(request, *args, **kwargs)

        if request.method == "GET":
            query_params = request.GET.copy()

            if "page" not in query_params:
                query_params["page"] = 1

            if query_params != request.GET and query_params["page"] != request.GET.get(
                "page"
            ):
                return redirect(
                    f"{reverse('leads:lead-list')}?{query_params.urlencode()}"
                )

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        category_name = self.request.GET.get("category", "").strip()
        unassigned_only = self.request.GET.get("unassigned_only")

        queryset = (
            Lead.objects.all()
            if user.is_organisor
            else Lead.objects.filter(agent__user=user)
        )

        if category_name:
            queryset = queryset.filter(category__name=category_name)

        if unassigned_only:
            queryset = queryset.filter(agent__isnull=True)

        return queryset.order_by("-date_created")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = self.get_queryset()
        paginator = Paginator(leads, self.paginate_by)
        page = self.request.GET.get("page", 1)

        try:
            paginated_leads = paginator.page(page)
        except PageNotAnInteger:
            paginated_leads = paginator.page(1)
        except EmptyPage:
            paginated_leads = paginator.page(paginator.num_pages)

        context["leads"] = paginated_leads
        context["form"] = CategoryFilterForm(self.request.GET)
        context["unassigned_only"] = self.request.GET.get("unassigned_only", False)

        if self.request.user.is_organisor:
            unassigned_leads = Lead.objects.filter(
                agent__isnull=True, category__name="new"
            )
            context["unassigned_leads"] = unassigned_leads

        return context

    def post(self, request, *args, **kwargs):
        """
        Handles the POST request to assign the oldest unassigned lead to the current agent.
        """
        user = self.request.user

        if not user.is_organisor and hasattr(user, "agent") and user.agent:
            oldest_unassigned_lead = (
                Lead.objects.filter(agent__isnull=True, category__name="new")
                .order_by("date_created")
                .first()
            )

            if oldest_unassigned_lead:
                oldest_unassigned_lead.agent = user.agent
                oldest_unassigned_lead.save()

                messages.success(
                    request,
                    f"You successfully took the lead: {oldest_unassigned_lead.first_name} {oldest_unassigned_lead.last_name}.",
                )
            else:
                messages.warning(request, "No unassigned leads available.")
        else:
            messages.error(request, "You are not authorized to take leads.")

        query_params = request.GET.urlencode()
        return redirect(f"{reverse('leads:lead-list')}?{query_params}")


# View to create a new lead.
class LeadCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_create.html"
    success_url = reverse_lazy("leads:lead-list")

    def form_valid(self, form):
        lead = form.save(commit=False)
        new_category = Category.objects.get(name="new")
        lead.category = new_category
        lead.save()

        messages.success(self.request, "You have successfully created a lead")
        return super().form_valid(form)


# View to show the details of a specific lead.
class LeadDetailView(LoginRequiredMixin, generic.DetailView):
    model = Lead
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(agent__user=user)
        return queryset

    def post(self, request, *args, **kwargs):
        lead = self.get_object()
        lead.comment = request.POST.get("comment", lead.comment)
        lead.save()
        return render(request, self.template_name, {"lead": lead})


# View to update details of an existing lead.
class LeadUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Lead
    form_class = None
    template_name = "leads/lead_update.html"
    success_url = reverse_lazy("leads:lead-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(agent__user=user)
        return queryset

    def get_form_class(self):
        # Returns a form class dynamically based on user role
        if self.request.user.is_organisor:
            return LeadForm
        return LeadAgentForm


# View to delete an existing lead.
class LeadDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Lead
    template_name = "leads/lead_delete.html"
    success_url = reverse_lazy("leads:lead-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(agent__user=user)
        return queryset


# Landing page view.
class LandingPageView(generic.TemplateView):
    template_name = "landing.html"


# Simple landing page view function.
def landing_page(request):
    return render(request, "landing.html")


# View to update the category of a lead.
class LeadCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(agent__user=user)
        return queryset

    def form_valid(self, form):
        lead = self.object

        if lead.convert:
            lead.is_converted = True
            lead.convert = False
            lead.save(update_fields=["is_converted", "convert"])

            if not lead.conversion_date:
                lead.conversion_date = now()
                lead.save(update_fields=["conversion_date"])

            # Save the updated category, if there is a change
            if form.cleaned_data.get("category"):
                lead.category = form.cleaned_data["category"]
                lead.save(update_fields=["category"])

            if lead.category and lead.category.name.lower() == "sale":
                client, created_client = Client.objects.get_or_create(
                    email=lead.email,
                    defaults={
                        "first_name": lead.first_name,
                        "last_name": lead.last_name,
                        "age": lead.age,
                        "phone_number": lead.phone_number,
                    },
                )

                if created_client:
                    client_url = reverse(
                        "clients:client-detail", args=[client.client_number]
                    )
                    messages.success(
                        self.request,
                        format_html(
                            "Lead converted successfully. A new client with client number {} was created. "
                            "Click <a href='{}' class='underline text-blue-500'>here</a> to view the client.",
                            client.client_number,
                            client_url,
                        ),
                    )
                else:
                    messages.info(
                        self.request,
                        f"Lead converted successfully, but the client with email {lead.email} already exists.",
                    )
            else:
                messages.success(self.request, "Lead converted successfully.")

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("leads:lead-detail", kwargs={"pk": self.object.pk})


# View to upload leads from an Excel file.
class LeadUploadView(OrganisorAndLoginRequiredMixin, View):
    template_name = "leads/lead_upload.html"

    def get(self, request, *args, **kwargs):
        form = LeadUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = LeadUploadForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data["file"]
            try:
                wb = openpyxl.load_workbook(file)
                sheet = wb.active

                skipped_rows = []
                duplicate_emails = []
                created_leads = 0
                new_category = Category.objects.get(name="new")

                for idx, row in enumerate(
                    sheet.iter_rows(min_row=2, values_only=True), start=2
                ):
                    first_name, last_name, age, email, phone_number = row[:5]

                    if not all([first_name, last_name, age, email, phone_number]):
                        skipped_rows.append(idx)
                        continue

                    if Lead.objects.filter(email=email).exists():
                        duplicate_emails.append(email)
                        continue

                    Lead.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        age=age,
                        email=email,
                        phone_number=phone_number,
                        category=new_category,
                    )
                    created_leads += 1

                messages.success(
                    request,
                    f"Successfully uploaded {created_leads} new leads. "
                    f"Skipped rows: {len(skipped_rows)}. "
                    f"Duplicate emails: {', '.join(duplicate_emails)}.",
                )
            except Exception as e:
                messages.error(request, f"Error uploading leads: {str(e)}")

        return render(request, self.template_name, {"form": form})
