from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from .models import Product
from .forms import ProductForm
from leads.models import Lead


class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        return Product.objects.filter(lead_id=self.kwargs["lead_id"])


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_create.html"

    def form_valid(self, form):
        lead = get_object_or_404(Lead, pk=self.kwargs["lead_id"])
        product = form.save(commit=False)
        product.lead = lead
        product.save()
        return redirect("leads:lead-detail", pk=lead.pk)


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_update.html"

    def get_success_url(self):
        return reverse_lazy(
            "products:product-list", kwargs={"lead_id": self.object.lead.pk}
        )


class ProductDeleteView(DeleteView):
    model = Product
    template_name = "products/product_delete.html"

    def get_success_url(self):
        return reverse_lazy(
            "products:product-list", kwargs={"lead_id": self.object.lead.pk}
        )
