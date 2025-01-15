from django.test import TestCase
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from leads.models import Agent


class AgentCreateViewTest(TestCase):
    def setUp(self):
        # Create an admin user (organisor)
        self.organisor_user = get_user_model().objects.create_user(
            username="organisor", password="testpassword", is_organisor=True
        )
        self.client.login(username="organisor", password="testpassword")

    def test_agent_create_view_status_code(self):
        """Test that the agent create view returns a 200 status code."""
        response = self.client.get(reverse("agents:agent-create"))
        self.assertEqual(response.status_code, 200)

    def test_agent_creation_and_email_sent(self):
        """Test that creating an agent sends an email and redirects correctly."""
        # Correct the test data
        data = {
            "username": "new_agent",  # Ensure this field is filled
            "email": "new_agent@example.com",  # Ensure this field is filled
            "first_name": "New",
            "last_name": "Agent",
            "password1": "password123",  # Passwords should match the model's form requirements
            "password2": "password123",
        }

        # Submit the form
        response = self.client.post(reverse("agents:agent-create"), data)

        # Check that the status code is a redirect (302)
        self.assertEqual(
            response.status_code, 302
        )  # Should redirect to agent list view

        # Check email sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Account Created in Dominik Jaroszuk CRM")
        self.assertIn("Your account has been successfully created.", email.body)

        # Ensure the agent was created in the database
        self.assertTrue(Agent.objects.filter(user__username="new_agent").exists())
