import openpyxl
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
    LeadCategoryUpdateForm,
    CategoryFilterForm,
    LeadUploadForm,
)
from django.shortcuts import render, reverse, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse("login")


class LeadListView(LoginRequiredMixin, generic.ListView):
    model = Lead
    template_name = "leads/lead-list.html"
    context_object_name = "leads"
    paginate_by = 9  # Set pagination to 10 leads per page

    def dispatch(self, request, *args, **kwargs):
        query_params = request.GET.copy()

        # Default `page` to 1 if missing
        if "page" not in query_params:
            query_params["page"] = 1

        # Redirect only if `page` is missing or invalid
        if query_params != request.GET:
            return redirect(f"{reverse('leads:lead-list')}?{query_params.urlencode()}")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Retrieves the filtered queryset based on the category and unassigned_only parameters.
        """
        user = self.request.user
        category_name = self.request.GET.get("category", "new").strip()
        unassigned_only = self.request.GET.get("unassigned_only")

        if user.is_organisor:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(agent__user=user)

        if category_name:
            queryset = queryset.filter(category__name=category_name)

        if unassigned_only:
            queryset = queryset.filter(agent__isnull=True)

        return queryset.order_by("-date_created")

    def get_context_data(self, **kwargs):
        """
        Adds custom pagination logic to the context.
        """
        context = super().get_context_data(**kwargs)

        # Get paginated queryset
        leads = self.get_queryset()
        paginator = Paginator(leads, self.paginate_by)
        page = self.request.GET.get("page", 1)

        try:
            paginated_leads = paginator.page(page)
        except PageNotAnInteger:
            paginated_leads = paginator.page(1)
        except EmptyPage:
            paginated_leads = paginator.page(paginator.num_pages)

        # Add paginated leads and filters to context
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
        if not user.is_organisor:  # Only agents can take a lead
            oldest_unassigned_lead = (
                Lead.objects.filter(agent__isnull=True, category__name="new")
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


class LeadCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_create.html"
    success_url = reverse_lazy("leads:lead-list")

    def form_valid(self, form):
        lead = form.save(commit=False)

        # Get the default "new" category for the current organisation
        new_category = Category.objects.get(name="new")

        # Assign the "new" category to the lead
        lead.category = new_category

        # Save the lead without assigning to an agent or organisation initially
        lead.save()

        # Success message
        messages.success(self.request, "You have successfully created a lead")
        return super().form_valid(form)


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
        lead = self.get_object()  # Retrieve the lead instance
        lead.comment = request.POST.get("comment", lead.comment)  # Update the comment
        lead.save()  # Save the updated lead
        return render(request, self.template_name, {"lead": lead})


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
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(agent__user=user)
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
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(agent__user=user)
        return queryset


class LandingPageView(generic.TemplateView):
    template_name = "landing.html"


def landing_page(request):
    return render(request, "landing.html")


class CategoryListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/category_list.html"
    context_object_name = "category_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Filter leads based on user type (organisor or agent)
        if user.is_organisor:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(agent__user=user)

        # Add unassigned lead count to the context
        context.update(
            {"unassigned_lead_count": queryset.filter(category__isnull=True).count()}
        )
        return context

    def get_queryset(self):
        queryset = Category.objects.all()
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
            queryset = Category.objects.all()  # Get all categories for the organiser
        else:
            queryset = Category.objects.filter(
                lead__agent__user=user
            )  # Get categories for agent
        return queryset


class LeadCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):

    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.all()  # All leads for the organiser
        else:
            # Agent leads filtered by the agent's profile
            queryset = Lead.objects.filter(agent__user=user)
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
                new_category = Category.objects.get(name="new")

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
                    if Lead.objects.filter(email=email).exists():
                        duplicate_emails.append(email)
                        continue

                    # Create the lead
                    Lead.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        age=int(age),
                        email=email,
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
