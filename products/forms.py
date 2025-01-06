from django import forms
from .models import Product
from datetime import datetime, timedelta


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "stock_quantity",
        ]


class ProductAssignmentForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["clients"]


class AddProductForm(forms.Form):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select Products",
    )


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
