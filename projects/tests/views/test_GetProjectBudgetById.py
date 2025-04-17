from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import WaletUser
from projects.models import Project, ProjectBudgetRecord
from uuid import uuid4

class GetProjectBudgetByIdTest(APITestCase):
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

        self.budget_record = ProjectBudgetRecord.objects.create(
            project=self.project,
            amount=5000,
            is_income=True,
            notes='Pemasukan awal',
            is_editable=True
        )

        self.token = self.get_user_token(self.manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.url = reverse('project-budget-detail', args=[self.budget_record.id])

    def get_user_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_get_project_budget_by_id_authenticated_manager(self):
        """Test manager can retrieve their own budget record by id."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.budget_record.id))
        self.assertEqual(response.data['amount'], 5000)
        self.assertEqual(response.data['notes'], 'Pemasukan awal')

    def test_get_project_budget_by_id_unauthenticated(self):
        """Test unauthenticated user cannot access budget record."""
        self.client.credentials() 
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_project_budget_by_id_other_user_forbidden(self):
        """Test non-manager cannot access the budget record."""
        token2 = self.get_user_token(self.other_user)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        url = reverse('project-budget-detail', args=[self.budget_record.id])
        response = other_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_project_budget_by_id_not_found(self):
        """Test 404 if budget record does not exist."""
        fake_id = uuid4()
        url = reverse('project-budget-detail', args=[fake_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
