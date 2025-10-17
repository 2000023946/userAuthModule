from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class TokenRefreshViewTests(APITransactionTestCase):
    """Tests for the default SimpleJWT TokenRefreshView."""

    databases = "__all__"

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email="user@example.com", password="Test1234", username="mon"
        )
        self.client = APIClient()
        self.url = reverse("token-refresh")  # Must match urls.py

        # Generate a valid refresh token
        refresh = RefreshToken.for_user(self.user)
        self.valid_refresh_token = str(refresh)
        self.invalid_refresh_token = "invalid-token"

    def test_invalid_refresh_token(self):
        """POST with an invalid token should return 401."""
        response = self.client.post(
            self.url, data={"refresh": self.invalid_refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("errors", response.data)
        self.assertTrue(response.data["errors"]["refresh"])  # Default SimpleJWT message

    def test_successful_refresh(self):
        """POST with a valid refresh token should return a new access token."""
        response = self.client.post(
            self.url, data={"refresh": self.valid_refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Optionally check that 'refresh' may also be returned
        self.assertIn("create", response.data)
        self.assertIn("refresh", response.data["create"])
