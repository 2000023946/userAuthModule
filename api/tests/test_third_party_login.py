from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from api.models import CustomUser


class ThirdPartyLoginTests(APITransactionTestCase):
    databases = "__all__"

    def setUp(self):
        # create a user matching the email that the third party will return
        self.email = "thirdparty@example.com"
        self.password = "dummy"
        self.user = CustomUser.objects.create(
            email=self.email,
            username="thirdpartyuser",
            password=make_password(self.password),
        )
        self.url = reverse("third-party-login")  # adjust to your url name

    @patch("api.views.ThirdPartyStrategySingleton.get_user_info")
    def test_third_party_login_success(self, mock_get_user_info):
        """
        Valid provider + token should return access & refresh tokens.
        """
        mock_get_user_info.return_value = {
            "email": self.email,
            "username": self.user.username,
        }

        payload = {"provider": "google", "token": "validtoken"}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("create", response.data)
        self.assertIn("refresh", response.data["create"])
        self.assertIn("access", response.data["create"])
        self.assertEqual(response.data["create"]["email"], self.email)

    @patch("api.views.ThirdPartyStrategySingleton.get_user_info")
    def test_third_party_login_invalid_token(self, mock_get_user_info):
        """
        Invalid token should return error from get_user_info.
        """
        mock_get_user_info.side_effect = ValueError("Invalid Google token")

        payload = {"provider": "google", "token": "badtoken"}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    def test_third_party_login_missing_fields(self):
        """
        Missing token or provider should return validation error.
        """
        payload = {"provider": "google"}  # no token
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
