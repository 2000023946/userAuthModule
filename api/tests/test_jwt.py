from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITransactionTestCase

User = get_user_model()


class JWTAuthTests(APITransactionTestCase):
    # 1. The "Guest List": Grants this test class PERMISSION to access all DBs.
    # This solves the `DatabaseOperationForbidden` error.
    databases = "__all__"

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email="test@example.com", username="momo", password="testpassword"
        )
        self.login_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")
        self.protected_url = reverse("protected_view")  # your protected API endpoint

    def test_login_returns_tokens(self):
        """
        Test that logging in returns access and refresh tokens
        """
        print("Users in the db ", User.objects.all())
        response = self.client.post(
            self.login_url,
            {
                "email": "test@example.com",
                "password": "testpassword",
                "username": "momo",
            },
            format="json",
        )
        print(response)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

    def test_access_token_can_access_protected_view(self):
        """
        Test that access token allows access to a protected endpoint
        """
        # First, get tokens
        response = self.client.post(
            self.login_url,
            {
                "email": "test@example.com",
                "password": "testpassword",
                "username": "momo",
            },
            format="json",
        )
        access_token = response.data["access"]

        # Use access token in header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hello", response.data["message"])

    def test_refresh_token_issues_new_access_token(self):
        """
        Test that refresh token returns a new access token
        """
        # Get tokens
        response = self.client.post(
            self.login_url,
            {
                "email": "test@example.com",
                "password": "testpassword",
                "username": "momo",
            },
            format="json",
        )
        refresh_token = response.data["refresh"]

        # Use refresh token to get new access token
        response = self.client.post(
            self.refresh_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        new_access_token = response.data["access"]
        self.assertNotEqual(new_access_token, "")  # token should not be empty
