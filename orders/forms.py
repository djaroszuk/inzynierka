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


class PaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
