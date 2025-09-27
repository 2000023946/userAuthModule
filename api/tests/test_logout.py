from django.urls import reverse
from rest_framework.test import APITestCase, APITransactionTestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django_redis import get_redis_connection
from unittest.mock import patch
from ..hasher import hash_token
from unittest.mock import call, patch
User = get_user_model()

class LogoutViewTests(APITransactionTestCase):
    databases = '__all__'
    def setUp(self):
        self.user = User.objects.create_user(email="testuser@example.com", password="TestPass123!", username='uaoi,ma')
        self.url = reverse("logout")  # make sure your URL name is "logout"
        self.client.force_authenticate(user=self.user)
        self.refresh = hash_token(str(RefreshToken.for_user(self.user)))
        self.access = hash_token(str(RefreshToken.for_user(self.user).access_token))

    @patch("django_redis.get_redis_connection")
    def test_logout_success(self, mock_redis):
        # Mock Redis connection
        mock_conn = mock_redis.return_value
        mock_conn.ttl.side_effect = lambda key: 3600  # 1 hour TTL

        response = self.client.post(
            self.url,
            {
                "refresh": str(self.refresh),
                "access": str(self.access)
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.data["message"], "Logout successful. Tokens invalidated.")
