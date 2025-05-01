from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import WaletUser
from projects.models import Project, ProjectBudgetRecord
from uuid import uuid4

class UpdateProjectBudgetTest(APITestCase):
    def setUp(self):
        self.manager = WaletUser.objects.create_user(
            username='manager',
            password='testpass',
            email='manager@example.com'
        )
        self.manager.is_active = True
        self.manager.save()

        self.other_user = WaletUser.objects.create_user(
            username='otheruser',
            password='testpass',
            email='other@example.com'
        )
        self.other_user.is_active = True
        self.other_user.save()

        self.project = Project.objects.create(
            manager=self.manager,
            name='Budget Project',
            total_budget=10000
        )

        self.editable_record = ProjectBudgetRecord.objects.create(
            project=self.project,
            amount=5000,
            is_income=True,
            notes='Editable',
            is_editable=True
        )
        self.uneditable_record = ProjectBudgetRecord.objects.create(
            project=self.project,
            amount=2000,
            is_income=True,
            notes='Uneditable',
            is_editable=False
        )

        self.token = self.get_user_token(self.manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def get_user_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_update_project_budget_success(self):
        """Test manager can update editable budget record."""
        url = reverse('edit-project-budget', args=[self.editable_record.id])
        data = {
            "amount": 6000,
            "notes": "Updated"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.editable_record.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.editable_record.amount, 6000)
        self.assertEqual(self.editable_record.notes, "Updated")
        self.assertEqual(self.project.total_budget, 11000)

    def test_update_project_budget_not_editable(self):
        """Test update fails if budget record is not editable."""
        url = reverse('edit-project-budget', args=[self.uneditable_record.id])
        data = {
            "amount": 3000,
            "notes": "Should not update"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.uneditable_record.refresh_from_db()
        self.assertEqual(self.uneditable_record.amount, 2000) 

    def test_update_project_budget_unauthenticated(self):
        """Test unauthenticated user cannot update budget record."""
        url = reverse('edit-project-budget', args=[self.editable_record.id])
        self.client.credentials()
        data = {
            "amount": 7000,
            "notes": "No Auth"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_project_budget_other_user(self):
        """Test non-manager cannot update budget record."""
        url = reverse('edit-project-budget', args=[self.editable_record.id])
        token2 = self.get_user_token(self.other_user)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        data = {
            "amount": 8000,
            "notes": "Other user"
        }
        response = other_client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.editable_record.refresh_from_db()
        self.assertEqual(self.editable_record.amount, 5000)  

    def test_update_project_budget_not_found(self):
        """Test 404 if budget record does not exist."""
        fake_id = uuid4()
        url = reverse('edit-project-budget', args=[fake_id])
        data = {
            "amount": 1234,
            "notes": "Not found"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
