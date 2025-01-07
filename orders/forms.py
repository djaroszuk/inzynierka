from django import forms


class StatisticsFilterForm(forms.Form):
    start_datetime = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control",
            }
        ),
        label="Start Date & Time",
    )
    end_datetime = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control",
            }
        ),
        label="End Date & Time",
    )

    def __init__(self, *args, **kwargs):
        super(StatisticsFilterForm, self).__init__(*args, **kwargs)
        # Removed logic for setting initial values


class OrderSearchForm(forms.Form):
    q = forms.CharField(
        label="Search by Order Number",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border rounded px-4 py-2 text-gray-700",
                "placeholder": "Enter order number",
            }
        ),
    )
