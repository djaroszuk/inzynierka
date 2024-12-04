import openpyxl
from django.core.mail import send_mail
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse_lazy
from django.views import generic, View
from agents.mixins import OrganisorAndLoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Lead, Category
from .forms import (
    LeadForm,
    CustomUserCreationForm,
    AssignAgentForm,
    LeadCategoryUpdateForm,
    CategoryFilterForm,
    LeadUploadForm,
)
from django.shortcuts import render, reverse, redirect


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse("login")


class LeadCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_create.html"
    success_url = reverse_lazy("leads:lead-list")

    def form_valid(self, form):
        lead = form.save(commit=False)
        lead.organisation = self.request.user.userprofile

        # Fetch the "new" category for the organization
        try:
            new_category = Category.objects.get(
                name="new", organisation=self.request.user.userprofile
            )
            lead.category = new_category  # Assign the "new" category
        except Category.DoesNotExist:
            messages.error(
                self.request,
                "The 'new' category is not available for this organization.",
            )
            return self.form_invalid(form)

        lead.save()

        # Send email notification
        send_mail(
            subject="A lead has been created",
            message="Go to the site to see the new lead",
            from_email="test@test.com",
            recipient_list=["test2@test.com"],
        )

        # Success message
        messages.success(self.request, "You have successfully created a lead")
        return super(LeadCreateView, self).form_valid(form)


class LeadListView(LoginRequiredMixin, generic.ListView):
    model = Lead
    template_name = "leads/lead-list.html"
    context_object_name = "leads"

    def get_queryset(self):
        user = self.request.user
        category_name = self.request.GET.get("category", "new")

        # Filter leads by organization and (for agents) by the agent itself
        queryset = Lead.objects.filter(organisation=user.userprofile)
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            queryset = queryset.filter(agent__user=user)

        # Apply category filter
        if category_name:
            queryset = queryset.filter(category__name=category_name)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Category filter form
        context["form"] = CategoryFilterForm(self.request.GET)

        # All categories for the user's organization
        context["categories"] = Category.objects.filter(organisation=user.userprofile)

        # Optionally include unassigned leads for the organizer
        if user.is_organisor:
            unassigned_leads = Lead.objects.filter(
                organisation=user.userprofile, agent__isnull=True
            )
            context.update({"unassigned_leads": unassigned_leads})

        return context

    def post(self, request, *args, **kwargs):
        user = self.request.user
        if not user.is_organisor:  # Only agents can take a lead
            # Find the oldest unassigned lead for the agent's organization
            oldest_unassigned_lead = (
                Lead.objects.filter(
                    organisation=user.agent.organisation, agent__isnull=True
                )
                .order_by("date_created")
                .first()
            )

            if oldest_unassigned_lead:
                # Assign the lead to the current agent
                oldest_unassigned_lead.agent = user.agent
                oldest_unassigned_lead.save()

                # Provide success feedback
                messages.success(
                    request,
                    f"You successfully took the lead: {oldest_unassigned_lead.first_name} {oldest_unassigned_lead.last_name}.",
                )
            else:
                # Provide feedback when no unassigned leads are available
                messages.warning(request, "No unassigned leads available.")
        return redirect("leads:lead-list")


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
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Filter leads based on user type (organisor or agent)
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)

        # Add unassigned lead count to the context
        context.update(
            {"unassigned_lead_count": queryset.filter(category__isnull=True).count()}
        )
        return context

    def get_queryset(self):
        user = self.request.user

        # Get categories based on user type (organisor or agent)
        if user.is_organisor:
            queryset = Category.objects.filter(organisation=user.userprofile)
        else:
            queryset = Category.objects.filter(organisation=user.agent.organisation)

        # Annotate categories with the count of associated leads
        return queryset.annotate(lead_count=Count("leads"))


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


class LeadUploadView(LoginRequiredMixin, View):
    template_name = "leads/lead_upload.html"

    def get(self, request, *args, **kwargs):
        form = LeadUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = LeadUploadForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data["file"]
            try:
                # Load the Excel file
                wb = openpyxl.load_workbook(file)
                sheet = wb.active

                skipped_rows = []  # Track rows with missing fields
                duplicate_emails = []  # Track duplicate email entries
                created_leads = 0  # Count successfully created leads
                new_category = Category.objects.get(
                    name="new", organisation=request.user.userprofile
                )

                # Process each row in the sheet (skip header row)
                for idx, row in enumerate(
                    sheet.iter_rows(min_row=2, values_only=True), start=2
                ):
                    first_name, last_name, age, email = row[:4]

                    # Skip rows with empty required fields
                    if not all([first_name, last_name, age, email]):
                        skipped_rows.append(idx)  # Add row number to skipped list
                        continue

                    # Check for duplicates
                    if Lead.objects.filter(
                        email=email, organisation=request.user.userprofile
                    ).exists():
                        duplicate_emails.append(email)
                        continue

                    # Create the lead
                    Lead.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        age=int(age),
                        email=email,
                        organisation=request.user.userprofile,
                        category=new_category,  # Assign the "new" category
                    )
                    created_leads += 1

                # Provide feedback after processing
                if skipped_rows:
                    messages.warning(
                        request,
                        f"Skipped rows due to missing fields: {', '.join(map(str, skipped_rows))}",
                    )
                if duplicate_emails:
                    messages.warning(
                        request,
                        f"Skipped {len(duplicate_emails)} rows due to duplicate emails: {', '.join(duplicate_emails)}",
                    )
                if created_leads:
                    messages.success(
                        request, f"Successfully imported {created_leads} leads!"
                    )
                if not skipped_rows and not duplicate_emails and created_leads == 0:
                    messages.info(request, "No leads were imported.")

            except Exception:
                messages.error(
                    request, "Error processing file: file is not an Excel file"
                )

        else:
            messages.error(request, "Invalid file. Please upload a valid Excel file.")

        # Always render the same page again with feedback messages
        return render(request, self.template_name, {"form": form})
