from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from decimal import Decimal
import uuid

from authentication.models import WaletUser
from funds.models import BudgetRequest, Project
from funds.serializers import BudgetRequestSerializer


class GetUserBudgetRequestsTest(APITestCase):
    """Test cases for the GetUserBudgetRequests API view."""

    def setUp(self):
        self.user1 = WaletUser.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123',
        )
        self.user2 = WaletUser.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123',
        )
    
        self.project1 = Project.objects.create(
            name='Project 1',
            description='First test project',
            manager_id=self.user1.id
        )
        self.project2 = Project.objects.create(
            name='Project 2',
            description='Second test project',
            manager_id=self.user2.id
        )
        
        self.budget_request1 = BudgetRequest.objects.create(
            project=self.project1,
            requested_by=self.user1,
            request_reason='Need funds for project 1',
            amount=Decimal('1000.00'),
            status='pending'
        )
        self.budget_request2 = BudgetRequest.objects.create(
            project=self.project1,
            requested_by=self.user1,
            request_reason='Additional funds for project 1',
            amount=Decimal('500.00'),
            status='approved'
        )
        self.budget_request3 = BudgetRequest.objects.create(
            project=self.project1,
            requested_by=self.user1,
            request_reason='Emergency funds for project 1',
            amount=Decimal('2000.00'),
            status='rejected'
        )
        
        self.budget_request4 = BudgetRequest.objects.create(
            project=self.project2,
            requested_by=self.user2,
            request_reason='Need funds for project 2',
            amount=Decimal('1500.00'),
            status='pending'
        )
        
        self.client = APIClient()
        
        self.url = reverse('budget-request-list') 

    def test_get_user_budget_requests_authentication_required(self):
        """Test that authentication is required to access the endpoint."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_budget_requests_success(self):
        """Test successful retrieval of user's budget requests."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(len(response.data), 3)
        
        budget_request_ids = [item['id'] for item in response.data]
        self.assertIn(str(self.budget_request1.id), budget_request_ids)
        self.assertIn(str(self.budget_request2.id), budget_request_ids)
        self.assertIn(str(self.budget_request3.id), budget_request_ids)
        
        self.assertNotIn(str(self.budget_request4.id), budget_request_ids)

    def test_get_user_budget_requests_filter_by_status(self):
        """Test filtering budget requests by status."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(f"{self.url}?status=pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.budget_request1.id))
        
        response = self.client.get(f"{self.url}?status=approved")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.budget_request2.id))
        
        response = self.client.get(f"{self.url}?status=rejected")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.budget_request3.id))
        
        response = self.client.get(f"{self.url}?status=invalid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_user_can_only_see_own_requests(self):
        """Test that a user can only see their own budget requests."""
        self.client.force_authenticate(user=self.user2)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.budget_request4.id))
        
        budget_request_ids = [item['id'] for item in response.data]
        self.assertNotIn(str(self.budget_request1.id), budget_request_ids)
        self.assertNotIn(str(self.budget_request2.id), budget_request_ids)
        self.assertNotIn(str(self.budget_request3.id), budget_request_ids)


class GetUserBudgetRequestsSecurityTest(APITestCase):
    """Security tests for the GetUserBudgetRequests API view."""

    def setUp(self):
        self.user1 = WaletUser.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123',
        )
        self.user2 = WaletUser.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123',
        )
        self.admin_user = WaletUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            description='Test project for security testing',
            manager_id=self.admin_user.id
        )
        
        self.budget_request1 = BudgetRequest.objects.create(
            project=self.project,
            requested_by=self.user1,
            request_reason='Confidential: Security audit for project',
            amount=Decimal('10000.00'),
            status='pending'
        )
        
        self.client = APIClient()
        
        self.url = reverse('budget-request-list')  

    def test_injection_in_status_parameter(self):
        """Test to ensure SQL injection via status parameter is not possible."""
        self.client.force_authenticate(user=self.user1)
        
        sql_injection = "pending' OR 1=1; --"
        response = self.client.get(f"{self.url}?status={sql_injection}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(len(response.data), 1)
        
        budget_request_ids = [item['id'] for item in response.data]
        self.assertIn(str(self.budget_request1.id), budget_request_ids)

    def test_insecure_direct_object_reference(self):
        """Test to ensure users cannot access other users' budget requests."""
    
        self.client.force_authenticate(user=self.user2)
    
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        
        budget_request_ids = [item['id'] for item in response.data] if response.data else []
        self.assertNotIn(str(self.budget_request1.id), budget_request_ids)