from django import forms
from django.contrib.auth import get_user_model

from clients.models import Client


User = get_user_model()


# Form for creating or updating Agent information
class AgentModelForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.required = True


# Form for creating and sending emails for organisor
class OrganisorEmailForm(forms.Form):
    subject = forms.CharField(max_length=100, required=True, label="Email Subject")
    message = forms.CharField(
        widget=forms.Textarea, required=True, label="Email Message"
    )
    send_to_all = forms.BooleanField(
        required=False,
        label="Send to All",
        help_text="Organizers can check this to send to all clients.",
        initial=False,
    )
    client_number = forms.CharField(
        required=False,
        label="Client Number",
        help_text="Provide the unique client number to email a specific client.",
    )

    def clean(self):
        cleaned_data = super().clean()
        send_to_all = cleaned_data.get("send_to_all")
        client_number = cleaned_data.get("client_number")

        # Validate that either 'send_to_all' or 'client_number' is provided
        if not send_to_all and not client_number:
            raise forms.ValidationError(
                "Either 'Send to All' must be checked or a Client Number must be provided."
            )

        # If client_number is provided, validate its existence
        if (
            client_number
            and not Client.objects.filter(client_number=client_number).exists()
        ):
            raise forms.ValidationError(
                {"client_number": "Client with this number does not exist."}
            )

        return cleaned_data


# Form for creating and sending emails for ogranisor
class AgentEmailForm(forms.Form):
    subject = forms.CharField(max_length=100, required=True, label="Email Subject")
    message = forms.CharField(
        widget=forms.Textarea, required=True, label="Email Message"
    )
    client_number = forms.CharField(
        required=True,
        label="Client Number",
        help_text="Provide the unique client number to email a specific client.",
    )

    def clean(self):
        cleaned_data = super().clean()
        client_number = cleaned_data.get("client_number")

        # Validate that client_number is provided and exists
        if not client_number:
            raise forms.ValidationError("Client Number is required.")
        if not Client.objects.filter(client_number=client_number).exists():
            raise forms.ValidationError(
                {"client_number": "Client with this number does not exist."}
            )

        return cleaned_data


# Form for searching agents
class AgentSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search Agents",
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 rounded px-4 py-2",
                "placeholder": "Search by username",
            }
        ),
    )
