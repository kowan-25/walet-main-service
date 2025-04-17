from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import WaletUser
from projects.models import Project, ProjectCategory, ProjectMember
from funds.models import Transaction

class CreateTransactionTest(APITestCase):
    def setUp(self):
        self.user = WaletUser.objects.create_user(
            username='user1',
            password='testpass',
            email='user1@example.com'
        )
        self.user.is_active = True
        self.user.save()

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

        self.token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.url = reverse('create-transaction') 

    def get_user_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_create_transaction_success(self):
        """Test successful transaction creation."""
        data = {
            "project_id": str(self.project.id),
            "amount": 1000,
            "transaction_note": "Test note",
            "category_id": str(self.category.id)
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], 1000)
        self.assertEqual(response.data['transaction_note'], "Test note")
        self.member.refresh_from_db()
        self.assertEqual(self.member.budget, 4000)

    def test_create_transaction_not_enough_budget(self):
        """Test transaction creation fails if budget is not enough."""
        data = {
            "project_id": str(self.project.id),
            "amount": 6000, 
            "transaction_note": "Test note",
            "category_id": str(self.category.id)
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "not enough amount")

    def test_create_transaction_invalid_input(self):
        """Test transaction creation with invalid input data."""
        data = {
            "project_id": str(self.project.id),
            "amount": -500,  
            "transaction_note": "Test note",
            "category_id": str(self.category.id)
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_create_transaction_unauthenticated(self):
        """Test unauthenticated user cannot create transaction."""
        self.client.credentials() 
        data = {
            "project_id": str(self.project.id),
            "amount": 1000,
            "transaction_note": "Test note",
            "category_id": str(self.category.id)
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)