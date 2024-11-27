from django import forms
from .models import Lead, Agent, Category
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth import get_user_model

User = get_user_model()


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


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)
        field_classes = {"username": UsernameField}


class AssignAgentForm(forms.Form):
    agent = forms.ModelChoiceField(queryset=Agent.objects.none())

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        agents = Agent.objects.filter(organisation=request.user.userprofile)
        super(AssignAgentForm, self).__init__(*args, **kwargs)
        self.fields["agent"].queryset = agents


class LeadCategoryUpdateForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ("category", "is_converted")


class CategoryFilterForm(forms.Form):
    category = forms.ChoiceField(
        choices=[("", "-- Select a Category --")]
        + [(category.name, category.name) for category in Category.objects.all()],
        required=False,
        label="Filter by Category",
    )


class LeadUploadForm(forms.Form):
    file = forms.FileField(
        label="Upload Excel File",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
