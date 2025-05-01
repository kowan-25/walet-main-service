from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import WaletUser
from projects.models import Project, ProjectBudgetRecord
from uuid import uuid4

class DeleteProjectBudgetTest(APITestCase):
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

    def test_delete_project_budget_success(self):
        """Test manager can delete editable budget record and total budget updated."""
        url = reverse('delete-project-budget', args=[self.editable_record.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ProjectBudgetRecord.objects.filter(pk=self.editable_record.id).exists())
        self.project.refresh_from_db()
        self.assertEqual(self.project.total_budget, 5000)

    def test_delete_project_budget_not_editable(self):
        """Test cannot delete uneditable budget record."""
        url = reverse('delete-project-budget', args=[self.uneditable_record.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(ProjectBudgetRecord.objects.filter(pk=self.uneditable_record.id).exists())

    def test_delete_project_budget_unauthenticated(self):
        """Test unauthenticated user cannot delete budget record."""
        url = reverse('delete-project-budget', args=[self.editable_record.id])
        self.client.credentials()  
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(ProjectBudgetRecord.objects.filter(pk=self.editable_record.id).exists())

    def test_delete_project_budget_other_user(self):
        """Test non-manager cannot delete budget record."""
        url = reverse('delete-project-budget', args=[self.editable_record.id])
        token2 = self.get_user_token(self.other_user)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        response = other_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(ProjectBudgetRecord.objects.filter(pk=self.editable_record.id).exists())

    def test_delete_project_budget_not_found(self):
        """Test 404 if budget record does not exist."""
        fake_id = uuid4()
        url = reverse('delete-project-budget', args=[fake_id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
