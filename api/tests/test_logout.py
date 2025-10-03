from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ..hasher import hash_token

User = get_user_model()


class LogoutViewTests(APITransactionTestCase):
    databases = "__all__"

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", password="TestPass123!", username="uaoi,ma"
        )
        self.url = reverse("logout")  # make sure your URL name is "logout"
        self.client.force_authenticate(user=self.user)
        self.refresh = hash_token(str(RefreshToken.for_user(self.user)))
        self.access = hash_token(str(RefreshToken.for_user(self.user).access_token))

    @patch("api.services.get_redis_connection")
    def test_logout_success(self, mock_redis):
        # Mock Redis connection
        mock_conn = mock_redis.return_value
        mock_conn.ttl.side_effect = lambda key: 3600  # 1 hour TTL

        response = self.client.post(
            self.url,
            {"refresh": str(self.refresh), "access": str(self.access)},
            format="json",
        )

        print(response, 'preposne', response.data)

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(
            response.data["message"], "Logout successful. Tokens invalidated."
        )
