# clients/forms.py
from django import forms
from .models import Client, Contact


class ClientForm(forms.ModelForm):
    """Form for non-organizer users."""

    class Meta:
        model = Client
        fields = ["first_name", "last_name", "age", "email", "phone_number"]
        labels = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "age": "Age",
            "email": "Email",
            "phone_number": "Phone Number",
        }


class OrganisorClientForm(ClientForm):
    """Extended form for organizers to include the 'status' field."""

    class Meta(ClientForm.Meta):
        fields = ClientForm.Meta.fields + ["status"]
        labels = {
            **ClientForm.Meta.labels,
            "status": "Status",
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ["reason", "description"]

    def __init__(self, *args, **kwargs):
        """Customize form appearance and initialization."""
        super().__init__(*args, **kwargs)
        self.fields["reason"].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update({"class": "form-control"})


class ClientSearchForm(forms.Form):
    q = forms.CharField(
        label="Search by Client Number",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border rounded px-4 py-2 text-gray-700",
                "placeholder": "Enter client number",
            }
        ),
    )
    important = forms.BooleanField(
        label="Important Clients Only",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"}),
    )
    last_contacted = forms.IntegerField(
        label="Last Sales Offer Contact (Days Ago)",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "border rounded px-4 py-2 text-gray-700",
                "placeholder": "Enter days ago",
            }
        ),
    )
