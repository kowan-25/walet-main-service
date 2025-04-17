from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
from projects.models import Project
from authentication.models import WaletUser

class SendFundsTestCase(APITestCase):
    def setUp(self):
        self.manager = WaletUser.objects.create_user(username='manager', email="manager@gmail.com", password='password')
        self.other_user = WaletUser.objects.create_user(username='member', email="member@gmail.com", password='password')
        self.project = Project.objects.create(
            manager=self.manager,
            name="Test Project",
            description="A test project",
            total_budget=1000,
            status=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager)
        self.url = reverse('send-funds', kwargs={'project_id': self.project.id})

    @patch('funds.views.send_funds')
    def test_send_funds_success(self, mock_send_funds):
        mock_send_funds.return_value = ({"message": "Funds sent"}, status.HTTP_200_OK)
        payload = {
            "member_id": str(self.other_user.id),
            "funds": 500,
            "notes": "For initial implementation"
        }

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Funds sent")
        mock_send_funds.assert_called_once_with(
            self.project.id, self.other_user.id, 500, "For initial implementation", self.manager.id
        )

    def test_send_funds_permission_denied(self):
        self.client.force_authenticate(user=self.other_user)
        payload = {
            "member_id": str(self.manager.id),
            "funds": 100,
            "notes": "Attempting unauthorized"
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You don't have permissions", str(response.data))
