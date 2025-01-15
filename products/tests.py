from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Product


User = get_user_model()


class ProductViewsTestCase(TestCase):

    def setUp(self):
        self.organisor_user = User.objects.create_user(
            username="organisor", password="password", is_organisor=True
        )
        self.client.login(username="organisor", password="password")
        self.product = Product.objects.create(name="Test Product", price=100.00)

    def test_product_list_view(self):
        """Test product list view."""
        response = self.client.get(reverse("products:product-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_list.html")
        self.assertContains(response, "Test Product")

    def test_product_detail_view(self):
        """Test product detail view."""
        response = self.client.get(
            reverse("products:product-detail", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_detail.html")
        self.assertContains(response, "Test Product")

    def test_product_delete_view(self):
        """Test widoku usuwania produktu."""
        response = self.client.get(
            reverse("products:product-delete", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_delete.html")

        # Usuwanie produktu
        response = self.client.post(
            reverse("products:product-delete", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(
            response.status_code, 302
        )  # Oczekujemy przekierowania na listę produktów
        self.assertRedirects(response, reverse("products:product-list"))
        self.assertEqual(Product.objects.count(), 0)  # Produkt został usunięty
