from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import WaletUser
from projects.models import Project, ProjectCategory, ProjectMember
from funds.models import Transaction
from uuid import uuid4

class DeleteTransactionTest(APITestCase):
    def setUp(self):
        self.user = WaletUser.objects.create_user(
            username='user1',
            password='testpass',
            email='user1@example.com'
        )
        self.user.is_active = True
        self.user.save()

        self.user2 = WaletUser.objects.create_user(
            username='user2',
            password='testpass',
            email='user2@example.com'
        )
        self.user2.is_active = True
        self.user2.save()

        # Create project, category, and member
        self.project = Project.objects.create(
            manager=self.user,
            name='Test Project',
            total_budget=10000
        )
        self.category = ProjectCategory.objects.create(
            project=self.project,
            name='Test Category'
        )
        self.member = ProjectMember.objects.create(
            project=self.project,
            member=self.user,
            budget=5000
        )

        # Create transaction for user1
        self.tx = Transaction.objects.create(
            user=self.user,
            project=self.project,
            amount=1000,
            transaction_category=self.category,
            transaction_note="To be deleted"
        )

        # Setup authentication for user1
        self.token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Endpoint URL
        self.url = reverse('delete-transaction', args=[self.tx.id])

    def get_user_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_delete_transaction_success(self):
        """Test successful transaction deletion and budget restored."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Transaction should be deleted
        self.assertFalse(Transaction.objects.filter(pk=self.tx.id).exists())
        # Budget should be restored
        self.member.refresh_from_db()
        self.assertEqual(self.member.budget, 6000)  # 5000 + 1000

    def test_delete_transaction_unauthenticated(self):
        """Test unauthenticated user cannot delete transaction."""
        self.client.credentials()  # Remove token
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_transaction_other_user(self):
        """Test that other users cannot delete this transaction."""
        token2 = self.get_user_token(self.user2)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        url = reverse('delete-transaction', args=[self.tx.id])
        response = other_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Transaction should still exist
        self.assertTrue(Transaction.objects.filter(pk=self.tx.id).exists())

    def test_delete_transaction_not_found(self):
        """Test 404 if transaction does not exist."""
        fake_id = uuid4()
        url = reverse('delete-transaction', args=[fake_id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
