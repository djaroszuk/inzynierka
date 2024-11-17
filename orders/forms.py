# orders/forms.py
from django import forms

from .models import Order, OrderProduct


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["client"]


OrderProductFormSet = forms.modelformset_factory(
    OrderProduct,
    fields=("product", "quantity"),
    extra=1,  # Number of additional empty forms to show
    can_delete=True,  # Allow deleting product entries
)
