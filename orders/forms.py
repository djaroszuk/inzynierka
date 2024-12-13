from django import forms
from django.utils import timezone


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

        # Check if the form is being rendered without any bound data
        if not self.is_bound:
            now = timezone.localtime(timezone.now())
            # Calculate the first day of the current month at 00:00
            first_day_of_month = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            # Format datetimes to 'YYYY-MM-DDTHH:MM' as expected by 'datetime-local' input
            self.fields["start_datetime"].initial = first_day_of_month.strftime(
                "%Y-%m-%dT%H:%M"
            )
            self.fields["end_datetime"].initial = now.strftime("%Y-%m-%dT%H:%M")
