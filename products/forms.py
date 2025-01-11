from django import forms
from .models import Product
from datetime import datetime, timedelta


# Form for adding or editing product
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "stock_quantity",
        ]


# Form for selecting months in last year
class TimeFrameSelectionForm(forms.Form):
    # Define the choices for the time frame
    TIMEFRAME_CHOICES = [
        ("last_30_days", "Last 30 Days"),
    ]

    # Add choices for each month of the last year
    current_date = datetime.now()
    for i in range(12):
        month_date = current_date - timedelta(days=30 * i)
        TIMEFRAME_CHOICES.append(
            (month_date.strftime("%Y-%m"), month_date.strftime("%B %Y"))
        )

    time_frame = forms.ChoiceField(
        choices=TIMEFRAME_CHOICES,
        label="Select Time Frame",
        required=True,
    )
