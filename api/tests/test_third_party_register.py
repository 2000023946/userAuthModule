from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from api.models import CustomUser

class ThirdPartyRegisterViewTests(APITestCase):
    def setUp(self):
        CustomUser.objects.all().delete()

        # Reset the client session
        session = self.client.session
        session.flush()  # clears all session data
        session.save()

        self.url = reverse('third-party-register')  # make sure your urls.py has this name
        self.provider = 'google'
        self.token = 'dummy-token'

    @patch('api.services.GoogleStrategy.get_user_info')
    def test_create_new_user_via_google(self, mock_get_user_info):
        """
        Should create a new user when email does not exist yet.
        """
        mock_get_user_info.return_value = {
            'email': 'newuser@example.com',
            'username': 'asd;ofjapsjlk'
        }

        resp = self.client.post(self.url, {
            'provider': self.provider,
            'token': self.token
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('create', resp.data)
        self.assertEqual(resp.data['create']['email'], 'newuser@example.com')

        self.assertTrue(CustomUser.objects.filter(email='newuser@example.com').exists())

    @patch('api.services.GoogleStrategy.get_user_info')
    def test_existing_user_via_google(self, mock_get_user_info):
        """
        Should update or return the existing user when email already exists.
        """
        existing = CustomUser.objects.create_user(
            email='existing@example.com',
            username='oldusername',
            password='testpass123'
        )

        mock_get_user_info.return_value = {
            'email': 'existing@example.com',
            'username': 'updatedusername'
        }

        resp = self.client.post(self.url, {
            'provider': self.provider,
            'token': self.token
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(resp.data['errors']['Email'])

        # Make sure the user was not duplicated
        self.assertEqual(CustomUser.objects.filter(email='existing@example.com').count(), 1)
