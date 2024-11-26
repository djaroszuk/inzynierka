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
