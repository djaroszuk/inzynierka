from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Lead, Category, Agent

User = get_user_model()


class LeadCreateViewTests(TestCase):

    def setUp(self):
        """
        Set up the test environment, including creating a user, category,
        and logging in the user.
        """
        self.organisor_user = User.objects.create_user(
            username="organisor", password="password", is_organisor=True
        )
        self.category, created = Category.objects.get_or_create(name="new")
        self.client.login(username="organisor", password="password")

    def test_lead_creation(self):
        """
        Test the creation of a lead by sending a POST request with lead data.
        Verify that the lead is created and displayed in the response.
        """
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 30,
            "email": "john.doe@example.com",
            "phone_number": "1234567890",
            "category": self.category.id,
        }
        response = self.client.post(reverse("leads:lead-create"), data, follow=True)
        self.assertEqual(Lead.objects.count(), 1)  # Ensure one lead is created
        self.assertEqual(response.status_code, 200)  # Verify the response status
        self.assertContains(response, "John Doe")  # Check if the new lead is shown


class LeadDeleteViewTests(TestCase):

    def setUp(self):
        """
        Set up the test environment, including creating a user, category,
        agent, lead, and logging in the user.
        """
        self.organisor_user = User.objects.create_user(
            username="organisor", password="password", is_organisor=True
        )
        self.category, created = Category.objects.get_or_create(name="new")
        self.agent = Agent.objects.create(user=self.organisor_user)
        self.lead = Lead.objects.create(
            first_name="Jane",
            last_name="Doe",
            age=25,
            email="jane.doe@example.com",
            phone_number="9876543210",
            category=self.category,
            agent=self.agent,
        )
        self.client.login(username="organisor", password="password")

    def test_lead_deletion(self):
        """
        Test the deletion of a lead. Send a POST request to delete the lead
        and verify the lead is removed from the database and the response is correct.
        """
        self.assertEqual(
            Lead.objects.count(), 1
        )  # Ensure the lead exists before deletion
        response = self.client.post(
            reverse("leads:lead-delete", kwargs={"pk": self.lead.pk}), follow=True
        )
        self.assertEqual(Lead.objects.count(), 0)  # Verify the lead is deleted
        self.assertEqual(
            response.status_code, 200
        )  # Ensure the correct response status
        self.assertNotContains(
            response, "Jane Doe"
        )  # Ensure the deleted lead is no longer displayed
