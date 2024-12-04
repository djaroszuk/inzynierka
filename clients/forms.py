# clients/forms.py
from django import forms
from .models import Client, Contact


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["first_name", "last_name", "age", "organisation", "agent"]


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
