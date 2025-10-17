from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class LogoutViewTests(APITransactionTestCase):
    databases = "__all__"

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", password="TestPass123!", username="uaoi,ma"
        )
        self.url = reverse("logout")
        self.client.force_authenticate(user=self.user)

        refresh = RefreshToken.for_user(self.user)
        self.refresh = str(refresh)
        self.access = str(refresh.access_token)

    def test_logout_success(self):
        """
        Test logout with real Redis connection.
        Tokens should be invalidated in Redis.
        """
        response = self.client.post(
            self.url,
            {"access": self.access, "refresh": self.refresh},
            format="json",
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(
            response.data["create"]["detail"], "Logout successful. Tokens invalidated."
        )
