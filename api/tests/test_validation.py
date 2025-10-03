from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITransactionTestCase

User = get_user_model()


class TokenRefreshViewTests(APITransactionTestCase):
    databases = "__all__"

    def setUp(self):
        """Set up the client and a test user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com", password="Test1234", username="mon"
        )
        self.url = "/token-refresh/"

    def test_missing_refresh_token(self):
        """Posting without a refresh token should return a 400 Bad Request."""
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Refresh token is required.")

    @patch("api.services.get_redis_connection")
    def test_blacklisted_token(self, mock_redis):
        """A blacklisted refresh token should return a 401 Unauthorized."""
        mock_conn = MagicMock()
        mock_conn.get.return_value = "true"
        mock_redis.return_value = mock_conn

        response = self.client.post(
            self.url, data={"refresh": "blacklisted-token"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Token is blacklisted.")

    @patch("api.services.get_redis_connection")
    def test_invalid_or_expired_refresh_token(self, mock_redis):
        """An invalid or expired (not in Redis cache) refresh token should return 401."""
        mock_conn = MagicMock()
        mock_conn.get.return_value = None
        mock_redis.return_value = mock_conn

        response = self.client.post(
            self.url, data={"refresh": "invalid-token"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Invalid or expired refresh token.")

    @patch("api.services.LoginBuilder")
    @patch("api.services.CustomUser.objects.get")
    @patch("api.services.RefreshToken")
    @patch("api.services.get_redis_connection")
    def test_successful_refresh_generates_new_tokens(
        self, mock_redis, mock_jwt_refresh, mock_get_user, mock_login_builder
    ):
        """A valid refresh token should return a new token pair and a 200 OK status."""
        mock_conn = mock_redis.return_value

        def redis_get_side_effect(key):
            if "blacklisted_token" in key:
                return None
            if "refresh_token" in key:
                return "1"

        mock_conn.get.side_effect = redis_get_side_effect
        mock_conn.ttl.return_value = 3600

        mock_jwt_refresh.return_value.get.return_value = self.user.id
        mock_get_user.return_value = self.user

        new_token_payload = {"refresh": "new_refresh_token", "access": "new_access_token"}
        mock_login_builder.return_value.build.return_value = new_token_payload

        valid_refresh_token = "valid-refresh-token"
        response = self.client.post(
            self.url, data={"refresh": valid_refresh_token}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, new_token_payload)

        mock_conn.set.assert_called_once_with(
            f"blacklisted_token:{valid_refresh_token}", "true", ex=3600
        )
