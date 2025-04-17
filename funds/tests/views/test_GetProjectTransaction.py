from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import WaletUser
from projects.models import Project, ProjectCategory
from funds.models import Transaction

class GetProjectTransactionTest(APITestCase):
    def setUp(self):
        self.user = WaletUser.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.user.is_active = True
        self.user.save()

        self.other_user = WaletUser.objects.create_user(
            username='otheruser',
            password='testpass',
            email='other@example.com'
        )
        self.other_user.is_active = True
        self.other_user.save()

        self.project = Project.objects.create(
            manager=self.user,
            name='Test Project',
            total_budget=1000
        )
        self.category = ProjectCategory.objects.create(
            project=self.project,
            name='Test Category'
        )
        self.transaction1 = Transaction.objects.create(
            user=self.user,
            project=self.project,
            amount=1000,
            transaction_category=self.category
        )
        self.transaction2 = Transaction.objects.create(
            user=self.user,
            project=self.project,
            amount=2000,
            transaction_category=self.category
        )

        self.token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.url = reverse('project-transaction-list', args=[self.project.id])

    def get_user_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_get_project_transactions_authenticated(self):
        """Test authenticated users can view project transactions."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_project_transactions_unauthenticated(self):
        """Test unauthenticated users cannot view transactions."""
        self.client.credentials()  
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_project_transactions_other_user(self):
        """Test that other users cannot view transactions from different projects."""
        other_client = APIClient()
        other_token = self.get_user_token(self.other_user)
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')
        response = other_client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_project_transactions_with_filtering(self):
        """Test that only transactions under the project are returned."""
        other_project = Project.objects.create(
            manager=self.other_user,
            name='Other Project',
            total_budget=500
        )
        other_category = ProjectCategory.objects.create(
            project=other_project,
            name='Other Category'
        )
        other_transaction = Transaction.objects.create(
            user=self.other_user,
            project=other_project,
            amount=3000,
            transaction_category=other_category
        )

        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 2)
        transaction_ids = [tx['id'] for tx in response.data]
        self.assertNotIn(str(other_transaction.id), transaction_ids)

    def test_get_project_transactions_with_pagination(self):
        """Test that all transactions are returned without pagination."""
        for _ in range(3):
            Transaction.objects.create(
                user=self.user,
                project=self.project,
                amount=500,
                transaction_category=self.category
            )
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 5)
