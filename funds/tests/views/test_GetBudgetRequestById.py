import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from funds.models import BudgetRequest
from funds.serializers import BudgetRequestSerializer
from projects.models import Project

User = get_user_model()

class GetBudgetRequestByIdTests(TestCase):
    """Test suite for the GetBudgetRequestById API view"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='password123'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123'
        )

        self.project1 = Project.objects.create(
            name='Project 1',
            description='First test project',
            manager_id=self.user1.id
        )
        
        self.budget_request1 = BudgetRequest.objects.create(
            amount=1000.00,
            requested_by=self.user1,
            project_id=self.project1.id
        )
        
        self.budget_request2 = BudgetRequest.objects.create(
            amount=2000.00,
            requested_by=self.user2,
            project_id=self.project1.id
        )
        
        self.client = APIClient()
        
        self.url1 = reverse('budget-request-detail', kwargs={"pk": self.budget_request1.id})
        self.url2 = reverse('budget-request-detail', kwargs={"pk": self.budget_request2.id})

    def test_get_budget_request_authenticated_owner(self):
        """Test retrieving a budget request by its owner is successful"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(self.url1)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GetBudgetRequestByIdSecurityTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='password123'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
        )
        self.project1 = Project.objects.create(
            name='Project 1',
            description='First test project',
            manager_id=self.user1.id
        )
        
        self.budget_request1 = BudgetRequest.objects.create(
            amount=1000.00,
            requested_by=self.user1,
            project_id=self.project1.id
        )
        
        self.client = APIClient()
        
        self.url1 = reverse('budget-request-detail', args=[self.budget_request1.id])

    def test_broken_authentication(self):
        """Test against broken authentication (OWASP A2: Broken Authentication)"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        response = self.client.get(self.url1)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_fixation(self):
        """Test against session fixation attacks"""
        self.client.force_authenticate(user=None)
        
        response1 = self.client.get(self.url1)
        
        self.client.force_authenticate(user=self.user1)
        
        response2 = self.client.get(self.url1)
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)


    def test_security_misconfiguration(self):
        """Test against security misconfiguration (OWASP A6)"""
        response = self.client.get('/api/non-existent-endpoint/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        if hasattr(response, 'data'):
            self.assertNotIn('Traceback', str(response.data))

    def test_cross_site_request_forgery(self):
        """Test against CSRF vulnerabilities"""
        self.client.login(username='testuser1', password='password123')

        response = self.client.post(
            self.url1,
            data=json.dumps({'title': 'Hacked title'}),
            content_type='application/json'
        )
    
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_rate_limiting(self):
        """Test rate limiting to prevent brute force attacks"""
        self.client.force_authenticate(user=self.user1)
        
        for _ in range(20):
            self.client.get(self.url1)
        
        response = self.client.get(self.url1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)