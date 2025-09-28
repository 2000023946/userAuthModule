from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from api.models import CustomUser


class LoginTests(APITransactionTestCase):
    databases = "__all__"

    def setUp(self):
        # Create a user we can log in with
        self.email = "user@example.com"
        self.password = "MyStrongPassword123"
        self.user = CustomUser.objects.create(
            email=self.email,
            username="testuser",
            password=make_password(self.password),
        )
        # endpoint you’ve wired up for login (adjust if different)
        self.url = reverse("login")  # in urls.py name='login'

    def test_login_success_returns_tokens(self):
        """
        Posting valid credentials should return refresh and access tokens.
        """
        payload = {"email": self.email, "password": self.password}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED
        )  # from AuthViews.mapping
        self.assertIn("create", response.data)
        self.assertIn("refresh", response.data["create"])
        self.assertIn("access", response.data["create"])
        self.assertEqual(response.data["create"]["email"], self.email)

    def test_login_invalid_password(self):
        """
        Posting wrong password should return an error.
        """
        payload = {"email": self.email, "password": "wrongpassword"}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    def test_login_missing_fields(self):
        """
        If only email is posted (first step), API should respond with a 'continue' message.
        """
        payload = {"email": self.email}  # no password yet

        response = self.client.post(self.url, payload, format="json")

        # Because the flow is multi-step, we expect HTTP 200 and a 'message'
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("Continue", response.data["message"])

    def test_login_wrong_password_second_step(self):
        """
        Post correct email first (step 1), then wrong password (step 2)
        should return 400 with an error message.
        """
        # Step 1: send email only
        response1 = self.client.post(self.url, {"email": self.email}, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertIn("message", response1.data)
        self.assertIn("Continue", response1.data["message"])

        # Step 2: send wrong password (state is stored in session)
        response2 = self.client.post(
            self.url, {"password": "wrongpassword"}, format="json"
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response2.data)
        # Optionally check that the error is under the Password state
        self.assertIn("Password", response2.data["errors"])
