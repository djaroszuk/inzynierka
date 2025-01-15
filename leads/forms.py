from django import forms
from .models import Lead, Category
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth import get_user_model
from django.db import OperationalError, ProgrammingError

# Get the custom User model

User = get_user_model()


# Form to create or update Lead entries
class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = (
            "first_name",
            "last_name",
            "age",
            "agent",
            "email",
            "phone_number",
        )


class LeadAgentForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = (
            "first_name",
            "last_name",
            "age",
            "email",
            "phone_number",
        )


# Custom form to handle user creation with email field
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")
        field_classes = {"username": UsernameField}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


# Form to update Lead category and conversion status
class LeadCategoryUpdateForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ("category", "convert")


try:
    CATEGORY_CHOICES = [
        (category.name, category.name) for category in Category.objects.all()
    ]
except (OperationalError, ProgrammingError):
    # If the table doesn't exist or is otherwise unavailable, use an empty list.
    CATEGORY_CHOICES = []


# Form for filtering leads by category
class CategoryFilterForm(forms.Form):
    category = forms.ChoiceField(
        choices=[("", "------")] + CATEGORY_CHOICES,
        required=False,
    )


# Form for uploading an Excel file
class LeadUploadForm(forms.Form):
    file = forms.FileField(
        label="Upload Excel File",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )


# Form to add comments to leads
class LeadCommentForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["comment"]
