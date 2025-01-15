from django.test import TestCase
from .models import Client


class ClientModelTest(TestCase):

    def test_generate_client_number(self):
        # Create a new client without specifying a client number
        client = Client(first_name="John", last_name="Doe")
        client.save()

        # Check that the client number is generated and is of length 8
        self.assertEqual(len(client.client_number), 8)
        self.assertTrue(client.client_number.isdigit())

    def test_client_creation(self):
        # Create a new client instance
        client = Client(
            first_name="David",
            last_name="Williams",
            age=30,
            email="david@example.com",
            phone_number="123-456-7890",
        )
        # Save the client instance to the database
        client.save()

        # Retrieve the client from the database
        retrieved_client = Client.objects.get(id=client.id)

        # Check if the client attributes match the values provided
        self.assertEqual(retrieved_client.first_name, "David")
        self.assertEqual(retrieved_client.last_name, "Williams")
        self.assertEqual(retrieved_client.age, 30)
        self.assertEqual(retrieved_client.email, "david@example.com")
        self.assertEqual(retrieved_client.phone_number, "123-456-7890")
