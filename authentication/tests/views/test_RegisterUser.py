from unittest.mock import patch
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from authentication.models import VerifyToken


User = get_user_model()


class RegisterUserTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register')  # make sure this name exists in your URLs

    @patch('authentication.views.requests.post')
    def test_register_user_success(self, mock_post):
        """Test user registration with valid input and successful email notification."""
        mock_post.return_value.status_code = 200
        data = {
            "username": "newuser",
            "email": "user@example.com",
            "password": "securePassword123?"
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(VerifyToken.objects.count(), 1)
        self.assertIn('user', response.data)
    
    @patch('authentication.views.requests.post')
    def test_register_user_failed_email(self, mock_post):
        """Test user registration with valid input and failed email notification."""
        mock_post.return_value.status_code = 500
        data = {
            "username": "newuser",
            "email": "user@example.com",
            "password": "securePassword123?"
        }

        with self.assertRaises(Exception) as context:
            self.client.post(self.url, data, format='json')

        self.assertTrue('Email service failed' in str(context.exception))
    
    @patch('authentication.views.requests.post')
    def test_register_user_invalid_input(self, mock_post):
        """Test user registration fails with invalid input (missing password)."""
        data = {
            "username": "newuser",
            "email": "user@example.com"
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)