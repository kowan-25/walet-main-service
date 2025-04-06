from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model


User = get_user_model()

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