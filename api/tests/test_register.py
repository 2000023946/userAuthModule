from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from api.models import CustomUser

class RegisterViewTests(APITestCase):
    from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase
from api.models import CustomUser  # adjust import to your actual user model

class RegistrationTests(APITransactionTestCase):
    databases = '__all__'
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
        Because registration is state-based, posting the full payload at once
        should not immediately create a user but should return an error dict
        with HTTP 400.
        """
        print('TESTING 1')
        url = reverse('register')
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "ValidPass123!",
            "password_repeat": "ValidPass123!"
        }

        response = self.client.post(url, payload, format='json')

        # Expect an error response (400) because state machine not finished
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check response structure
        self.assertIn('errors', response.data)
        self.assertIsInstance(response.data['errors'], dict)

        # User should not yet exist
        self.assertFalse(CustomUser.objects.filter(username="newuser").exists())
        print('TESTING 1 PASSED')

    def test_register_creates_user_step_by_step(self):
        """
        Posting valid registration data step by step should create a new CustomUser
        and return 201 status with user data.
        """
        url = reverse('register')

        # 1. send username only
        response = self.client.post(url, {"username": "nklajomo"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # 2. send email
        response = self.client.post(url, {"email": "newuser@example.com"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. send password
        response = self.client.post(url, {"password": "ValidPass123!"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. send password_repeat (should complete registration)
        response = self.client.post(url, {"password_repeat": "ValidPass123!"}, format='json')

        # registration complete
        self.assertIn(response.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))

        # user exists in DB
        self.assertTrue(CustomUser.objects.filter(username="nklajomo").exists())
        user = CustomUser.objects.get(username="nklajomo")
        self.assertEqual(user.email, "newuser@example.com")

        # check response correctly
        self.assertIn('create', response.data)
        self.assertIn('email', response.data['create'])
        self.assertEqual(response.data['create']['email'], "newuser@example.com")

    def test_register_fails_on_password_mismatch(self):
        url = reverse('register')

        # Step 1: username
        self.client.post(url, {"username": "user123"}, format='json')
        # Step 2: email
        self.client.post(url, {"email": "user@example.com"}, format='json')
        # Step 3: password
        self.client.post(url, {"password": "ValidPass123!"}, format='json')
        # Step 4: password_repeat (mismatch)
        response = self.client.post(url, {"password_repeat": "WrongPass123!"}, format='json')

        # Should return an error because passwords do not match
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('PasswordRepeat', response.data['errors'])
        self.assertFalse(CustomUser.objects.filter(username="user123").exists())

    def test_register_fails_if_username_similar_to_email(self):
        url = reverse('register')

        # Step 1: username (too similar to email)
        self.client.post(url, {"username": "user@example.com"}, format='json')
        # Step 2: email
        response = self.client.post(url, {"email": "user@example.com"}, format='json')

        # Should fail due to similarity check
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('Username', response.data['errors'])
        self.assertFalse(CustomUser.objects.filter(username="user@example.com").exists())

    def test_invalid_email_format(self):
        """
        Sending an invalid email should return an error.
        """
        url = reverse('register')
        self.client.post(url, {"username": "user1"}, format='json')
        response = self.client.post(url, {"email": "invalid-email"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('Email', response.data['errors'])
        self.assertFalse(CustomUser.objects.exists())

    def test_invalid_username(self):
        """
        Sending a username with invalid characters or length should fail.
        """
        url = reverse('register')
        response = self.client.post(url, {"username": "ab"}, format='json')  # too short

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('Username', response.data['errors'])

    def test_duplicate_username_or_email(self):
        """
        Creating a user with an existing username or email should fail.
        """
        # First user
        user = CustomUser.objects.create(username="userdup", email="dup@example.com", password="ValidPass123!")
        url = reverse('register')
        self.client.post(url, {"username": "userdup"}, format='json')
        response = self.client.post(url, {"email": "dup@example.com"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)

    def test_resume_registration_from_session(self):
        """
        If a user partially fills registration and resumes later,
        the session should correctly resume at the next state.
        """
        url = reverse('register')
        # Step 1: send username
        self.client.post(url, {"username": "resumeuser"}, format='json')
        # Simulate a new request with same session
        response = self.client.post(url, {"email": "resume@example.com"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertNotIn('errors', response.data)








