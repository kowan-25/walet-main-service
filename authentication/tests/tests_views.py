import uuid
from unittest.mock import patch
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from authentication.models import VerifyToken, WaletUser  # adjust import as needed


User = get_user_model()


class RegisterUserTestCase(TestCase):
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


class VerifyUserTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="verifyme", email="verify@example.com", is_active=False)
        self.token = VerifyToken.objects.create(user_id=self.user.id)
        self.url = reverse('verify-user', kwargs={"verify_id": str(self.token.id)})

    def test_verify_user_success(self):
        """Test successful user verification by verify ID."""
        response = self.client.post(self.url)

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.is_active)
        self.assertFalse(VerifyToken.objects.filter(id=self.token.id).exists())

    def test_verify_user_already_active(self):
        """Test verify fails if user is already active."""
        self.user.is_active = True
        self.user.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_verify_user_invalid_token(self):
        """Test 404 if verify token does not exist."""
        url = reverse('verify-user', kwargs={"verify_id": uuid.uuid4()})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LoginUserTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="loginuser", email="login@example.com", password="loginpass")
        self.user.is_active = True
        self.user.save()
        self.url = reverse('login')

    def test_login_success(self):
        """Test login returns tokens on correct credentials."""
        data = {
            "username": "loginuser",
            "password": "loginpass"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_invalid_credentials(self):
        """Test login fails with incorrect credentials."""
        data = {
            "username": "loginuser",
            "password": "wrongpassword"
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
