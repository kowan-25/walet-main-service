import uuid
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from authentication.models import VerifyToken

User = get_user_model()

class VerifyUserTest(TestCase):
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