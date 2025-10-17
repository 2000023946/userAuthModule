from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from api.models import CustomUser


class PasswordResetTests(APITransactionTestCase):
    databases = "__all__"

    def setUp(self):
        # Clear session
        session = self.client.session
        session.clear()
        session.save()

        # Clear existing users and create a test user
        CustomUser.objects.all().delete()
        self.user = CustomUser.objects.create_user(
            username="testuser", email="testuser@example.com", password="OldPass123!"
        )

    # def test_password_reset_step_by_step(self):
    #     """Step-by-step password reset should update the user's password."""
    #     url = reverse("password-reset")
    #     print(self.user.check_password("OldPass123!"), self.user.check_password("NewPass123!"))

    #     # 1. send email only
    #     response = self.client.post(
    #         url, {"email": "testuser@example.com"}, format="json"
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertIn("message", response.data)

    #     # 2. send new password
    #     response = self.client.post(url, {"password": "NewPass123!", 'jwt':response.data['jwt']}, format="json")
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    #     # 3. send password_repeat (complete reset)
    #     response = self.client.post(
    #         url, {"password_repeat": "NewPass123!", 'jwt': response.data['jwt']}, format="json"
    #     )
    #     self.assertIn(
    #         response.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED)
    #     )
    #     self.assertIn("create", response.data)
    #     print(response.data)

    #     # verify password updated
    #     self.user.refresh_from_db()
    #     print(self.user.check_password("OldPass123!"), self.user.check_password("NewPass123!"))
    #     self.assertTrue(self.user.check_password("NewPass123!"))

    # def test_password_reset_full_payload(self):
    #     """Sending full payload at once should succeed if valid."""
    #     url = reverse("password-reset")
    #     payload = {
    #         "email": "testuser@example.com",
    #         "password": "NewPass123!",
    #         "password_repeat": "NewPass123!",
    #     }

    #     response = self.client.post(url, payload, format="json")

    #     # Expect success (200 or 201)
    #     self.assertIn(
    #         response.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED)
    #     )

    #     # Should not contain errors
    #     self.assertNotIn("errors", response.data)

    #     # Check that the password was actually updated
    #     user = CustomUser.objects.get(email="testuser@example.com")
    #     self.assertTrue(user.check_password("NewPass123!"))

    def test_password_reset_password_mismatch(self):
        """Password and password_repeat mismatch should return error."""
        url = reverse("password-reset")
        response = self.client.post(
            url, {"email": "testuser@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            url, {"password": "NewPass123!", "jwt": response.data["jwt"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # wrong repeat
        response = self.client.post(
            url,
            {"password_repeat": "Mismatch123!", "jwt": response.data["jwt"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    def test_password_reset_missing_fields(self):
        """Missing required fields should raise errors."""
        url = reverse("password-reset")
        response = self.client.post(url, {"password": "NewPass123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
