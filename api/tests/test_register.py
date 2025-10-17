from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from api.models import CustomUser  # adjust import if needed


class RegistrationTests(APITransactionTestCase):
    """
    Test the registration view step-by-step and error cases.
    """

    databases = "__all__"

    def setUp(self):
        """
        Clear session and database before each test.
        """
        # Clear session
        session = self.client.session
        session.clear()
        session.save()

        # Clear any existing users
        CustomUser.objects.all().delete()

    def test_register_returns_error_for_full_payload(self):
        """
        Posting the full payload at once should not immediately create a user.
        """
        url = reverse("register")
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "ValidPass123!",
            "password_repeat": "ValidPass123!",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertIsInstance(response.data["errors"], dict)
        self.assertFalse(CustomUser.objects.filter(username="newuser").exists())

    def test_register_creates_user_step_by_step(self):
        """
        Posting valid registration data step by step should create a new user.
        """
        url = reverse("register")

        # 1. send username only
        response = self.client.post(url, {"username": "nklajomo"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # 2. send email
        response = self.client.post(
            url,
            {"email": "newuser@example.com", "jwt": response.data["jwt"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. send password
        response = self.client.post(
            url,
            {"password": "ValidPass123!", "jwt": response.data["jwt"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. send password_repeat (should complete registration)
        response = self.client.post(
            url,
            {"password_repeat": "ValidPass123!", "jwt": response.data["jwt"]},
            format="json",
        )

        self.assertIn(
            response.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK)
        )
        self.assertTrue(CustomUser.objects.filter(email="newuser@example.com").exists())
        user = CustomUser.objects.get(email="newuser@example.com")
        self.assertEqual(user.email, "newuser@example.com")

        self.assertIn("create", response.data)
        self.assertIn("email", response.data["create"])
        self.assertEqual(response.data["create"]["email"], "newuser@example.com")

    def test_register_fails_on_password_mismatch(self):
        url = reverse("register")

        response = self.client.post(url, {"username": "usqe23r123"}, format="json")
        response = self.client.post(
            url,
            {"email": "user@example.com", "jwt": response.data["jwt"]},
            format="json",
        )
        response = self.client.post(
            url,
            {"password": "ValidPass123!", "jwt": response.data["jwt"]},
            format="json",
        )
        response = self.client.post(
            url,
            {"password_repeat": "WrongPass123!", "jwt": response.data["jwt"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertIn("CompleteRegistration", response.data["errors"])
        self.assertFalse(CustomUser.objects.filter(username="user123").exists())

    def test_invalid_email_format(self):
        """
        Sending an invalid email should return an error.
        """
        url = reverse("register")
        response = self.client.post(url, {"username": "user1"}, format="json")
        response = self.client.post(
            url, {"email": "invalid-email", "jwt": response.data["jwt"]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertIn("Email", response.data["errors"])
        self.assertFalse(CustomUser.objects.exists())

    def test_invalid_username(self):
        """
        Sending a username with invalid characters or length should fail.
        """
        url = reverse("register")
        response = self.client.post(url, {"username": "ab"}, format="json")  # too short

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertIn("Username", response.data["errors"])

    def test_duplicate_username_or_email(self):
        """
        Creating a user with an existing username or email should fail.
        """
        CustomUser.objects.create(
            username="userdup", email="dup@example.com", password="ValidPass123!"
        )
        url = reverse("register")
        response = self.client.post(url, {"username": "userdup"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    def test_resume_registration_from_session(self):
        """
        If a user partially fills registration and resumes later,
        the session should correctly resume at the next state.
        """
        url = reverse("register")
        response = self.client.post(url, {"username": "resumeuser"}, format="json")
        response = self.client.post(
            url,
            {"email": "resume@example.com", "jwt": response.data["jwt"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertNotIn("errors", response.data)
