import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import WaletUser
from projects.models import Project, ProjectCategory
from funds.models import Transaction

class GetMemberTransactionTest(APITestCase):
    def setUp(self):
        self.user1 = WaletUser.objects.create_user(
            username='user1',
            password='testpass',
            email='user1@example.com'
        )
        self.user1.is_active = True
        self.user1.save()

        self.user2 = WaletUser.objects.create_user(
            username='user2',
            password='testpass',
            email='user2@example.com'
        )
        self.user2.is_active = True
        self.user2.save()

        self.project = Project.objects.create(
            manager=self.user1,
            name='Test Project',
            total_budget=1000
        )
        self.category = ProjectCategory.objects.create(
            project=self.project,
            name='Test Category'
        )

        self.tx1 = Transaction.objects.create(
            user=self.user1,
            project=self.project,
            amount=1000,
            transaction_category=self.category
        )
        self.tx2 = Transaction.objects.create(
            user=self.user1,
            project=self.project,
            amount=2000,
            transaction_category=self.category
        )

        self.token1 = self.get_user_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')

    def get_user_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_get_member_transactions_valid_access(self):
        """Test authenticated user can view their own transactions."""
        url = reverse('member-transaction-list', args=[self.project.id, self.user1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) 

    def test_get_member_transactions_unauthorized_access(self):
        """Test other users cannot view transactions from different users."""
        self.token2 = self.get_user_token(self.user2)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token2}')

        url = reverse('member-transaction-list', args=[self.project.id, self.user1.id])
        response = other_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_member_transactions_non_existent_user(self):
        """Test handling non-existent user."""
        fake_user_id = uuid.uuid4()
        url = reverse('member-transaction-list', args=[self.project.id, fake_user_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_member_transactions_empty_transactions(self):
        """Test empty transaction list."""
        Transaction.objects.filter(user=self.user1).delete()
        url = reverse('member-transaction-list', args=[self.project.id, self.user1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_member_transactions_with_filtering(self):
        """Test filtering berdasarkan project dan user."""
        tx3 = Transaction.objects.create(
            user=self.user2,
            project=self.project,
            amount=3000,
            transaction_category=self.category
        )

        url = reverse('member-transaction-list', args=[self.project.id, self.user1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) 
        transaction_ids = [tx['id'] for tx in response.data]
        self.assertNotIn(str(tx3.id), transaction_ids)

    def test_get_member_transactions_with_pagination(self):
        """Test pagination jika diimplementasikan."""
        for _ in range(3):
            Transaction.objects.create(
                user=self.user1,
                project=self.project,
                amount=500,
                transaction_category=self.category
            )
        url = reverse('member-transaction-list', args=[self.project.id, self.user1.id])
        response = self.client.get(url)
        self.assertEqual(len(response.data), 5)  
