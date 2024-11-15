from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "price"]


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
