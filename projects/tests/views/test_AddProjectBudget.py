from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import WaletUser
from projects.models import Project, ProjectBudgetRecord

class AddProjectBudgetTest(APITestCase):
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

        self.token = self.get_user_token(self.manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.url = reverse('create-project-budget')

    def get_user_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_add_project_budget_income_success(self):
        """Test manager can add an income budget record."""
        data = {
            "project_id": str(self.project.id),
            "amount": 5000,
            "notes": "Pemasukan awal"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        self.assertTrue(ProjectBudgetRecord.objects.filter(project=self.project, amount=5000, notes="Pemasukan awal").exists())

    def test_add_project_budget_expense_success(self):
        """Test manager can add an expense budget record with member."""
        data = {
            "project_id": str(self.project.id),
            "amount": 2000,
            "notes": "Pengeluaran"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

    def test_add_project_budget_unauthenticated(self):
        """Test unauthenticated user cannot add budget record."""
        self.client.credentials() 
        data = {
            "project_id": str(self.project.id),
            "amount": 1000,
            "notes": "Unauthorized"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_project_budget_invalid_input(self):
        """Test invalid input (negative amount) is rejected."""
        data = {
            "project_id": str(self.project.id),
            "amount": -1000,
            "notes": "Negatif"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_project_budget_not_manager(self):
        """Test non-manager cannot add budget record to project."""
        token2 = self.get_user_token(self.other_user)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        data = {
            "project_id": str(self.project.id),
            "amount": 1000,
            "notes": "Not manager"
        }
        response = other_client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
