from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
from uuid import uuid4
from projects.models import Project
from authentication.models import WaletUser


class TakeFundsTestCase(APITestCase):
    def setUp(self):
        self.user = WaletUser.objects.create_user(username='testuser', email="test@gmail.com", password='password')
        self.member = WaletUser.objects.create_user(username='memberuser', email="member@gmail.com", password='password')
        self.project = Project.objects.create(
            manager=self.user,
            name="Another Project",
            description="Testing take funds",
            total_budget=2000,
            status=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('take-funds', kwargs={'project_id': self.project.id})

    @patch('funds.views.take_funds')
    def test_take_funds_success(self, mock_take_funds):
        mock_take_funds.return_value = ({"message": "Funds taken"}, status.HTTP_200_OK)
        payload = {
            "member_id": str(self.member.id),
            "funds": 300,
            "notes": "For logistics"
        }

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Funds taken")
        mock_take_funds.assert_called_once_with(
            self.project.id, self.member.id, 300, "For logistics", self.user.id
        )

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        payload = {
            "member_id": str(self.member.id),
            "funds": 100,
            "notes": "No auth"
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
