from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import WaletUser
from projects.models import Project, ProjectCategory, ProjectMember
from funds.models import Transaction
from uuid import uuid4

class UpdateTransactionTest(APITestCase):
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

        self.tx = Transaction.objects.create(
            user=self.user,
            project=self.project,
            amount=1000,
            transaction_category=self.category,
            transaction_note="Old note"
        )

        self.token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.url = reverse('edit-transaction', args=[self.tx.id])

    def get_user_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_update_transaction_success(self):
        """Test successful transaction update."""
        data = {
            "amount": 2000,
            "transaction_note": "Updated note",
            "category_id": str(self.category.id)
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tx.refresh_from_db()
        self.assertEqual(self.tx.amount, 2000)
        self.assertEqual(self.tx.transaction_note, "Updated note")
        self.member.refresh_from_db()
        self.assertEqual(self.member.budget, 4000)

    def test_update_transaction_not_enough_budget(self):
        """Test update fails if budget is not enough."""
        data = {
            "amount": 7000, 
            "transaction_note": "Updated note",
            "category_id": str(self.category.id)
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "not enough amount")

    def test_update_transaction_invalid_input(self):
        """Test update fails with invalid input (negative amount)."""
        data = {
            "amount": -1500,
            "transaction_note": "Updated note",
            "category_id": str(self.category.id)
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_update_transaction_unauthenticated(self):
        """Test unauthenticated user cannot update transaction."""
        self.client.credentials()  
        data = {
            "amount": 2000,
            "transaction_note": "Updated note",
            "category_id": str(self.category.id)
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_transaction_other_user(self):
        """Test that other users cannot update this transaction."""
        token2 = self.get_user_token(self.user2)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        data = {
            "amount": 2000,
            "transaction_note": "Updated note",
            "category_id": str(self.category.id)
        }
        url = reverse('edit-transaction', args=[self.tx.id])
        response = other_client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_transaction_not_found(self):
        """Test 404 if transaction does not exist."""
        fake_id = uuid4()
        url = reverse('edit-transaction', args=[fake_id])
        data = {
            "amount": 2000,
            "transaction_note": "Updated note",
            "category_id": str(self.category.id)
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
