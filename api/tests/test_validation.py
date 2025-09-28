from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITransactionTestCase

User = get_user_model()


class TokenValidationViewTests(APITransactionTestCase):
    databases = "__all__"

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com", password="Test1234", username="mon"
        )
        # Set up a session with jti
        session = self.client.session
        session["jti"] = "test-jti"
        session.save()

    def test_missing_tokens(self):
        """If access or refresh token is missing"""
        response = self.client.post("/token-validation/", data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Tokens required")

    def test_missing_session_jti(self):
        """If session has no jti"""
        session = self.client.session
        session.pop("jti", None)
        session.save()

        response = self.client.post(
            "/token-validation/", data={"access": "a", "refresh": "r"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Session expired")

    @patch("api.views.get_redis_connection")
    def test_blacklisted_tokens(self, mock_redis):
        """If either access or refresh token is blacklisted"""
        mock_conn = MagicMock()
        mock_conn.get.side_effect = lambda key: (
            "something" if "black_list" in key else None
        )
        mock_redis.return_value = mock_conn

        response = self.client.post(
            "/token-validation/", data={"access": "a", "refresh": "r"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Expired Tokens")

    @patch("api.views.get_redis_connection")
    def test_valid_access_token(self, mock_redis):
        """If access token exists (still valid)"""
        mock_conn = MagicMock()
        mock_conn.get.side_effect = lambda key: (
            "hash" if "access_token" in key else None
        )
        mock_redis.return_value = mock_conn

        response = self.client.post(
            "/token-validation/", data={"access": "a", "refresh": "r"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Success access token valid")

    @patch("api.views.get_redis_connection")
    @patch("api.views.LoginBuilder.build")
    def test_expired_access_valid_refresh_generates_new_tokens(
        self, mock_build, mock_redis
    ):
        """If access expired but refresh valid, generates new tokens"""
        mock_conn = MagicMock()

        def get_side_effect(key):
            if key.startswith("access_token"):
                return None
            if key.startswith("refresh_token"):
                return "hash"
            return None

        mock_conn.get.side_effect = get_side_effect
        mock_conn.ttl.return_value = 3600
        mock_redis.return_value = mock_conn

        mock_build.return_value = {
            "refresh": "new_refresh",
            "access": "new_access",
            "email": self.user.email,
        }

        response = self.client.post(
            "/token-validation/",
            data={"access": "expired-access", "refresh": "valid-refresh"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("details", response.data)
        self.assertEqual(response.data["details"]["email"], self.user.email)
        # Ensure refresh token was blacklisted with correct TTL
        mock_conn.set.assert_any_call(
            "black_list:valid-refresh", "valid-refresh", ex=3600
        )

    @patch("api.views.get_redis_connection")
    def test_invalid_refresh_token(self, mock_redis):
        """If refresh token is expired"""
        mock_conn = MagicMock()

        # access token missing, refresh token missing
        def get_side_effect(key):
            if key.startswith("access_token"):
                return None
            if key.startswith("refresh_token"):
                return None
            return None

        mock_conn.get.side_effect = get_side_effect
        mock_redis.return_value = mock_conn

        response = self.client.post(
            "/token-validation/",
            data={"access": "expired-access", "refresh": "expired-refresh"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid Refresh Token")
