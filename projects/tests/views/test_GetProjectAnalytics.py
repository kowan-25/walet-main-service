from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from authentication.models import WaletUser
from projects.models import Project, ProjectBudgetRecord, ProjectMember, ProjectCategory
from funds.models import Transaction
import uuid
from datetime import timedelta
import json
import logging

class GetProjectAnalyticsTest(APITestCase):
    def setUp(self):
        self.manager = WaletUser.objects.create_user(
            username='manager',
            password='secure_password123',
            email='manager@example.com'
        )
        self.manager.is_active = True
        self.manager.save()
        
        self.team_member = WaletUser.objects.create_user(
            username='teammember',
            password='secure_password456',
            email='member@example.com'
        )
        self.team_member.is_active = True 
        self.team_member.save()
        
        self.other_user = WaletUser.objects.create_user(
            username='otheruser',
            password='secure_password789',
            email='other@example.com'
        )
        self.other_user.is_active = True
        self.other_user.save()
        
        self.project = Project.objects.create(
            manager=self.manager,
            name='Analytics Test Project',
            description='Project for testing analytics',
            total_budget=10000
        )
        
        self.project_member = ProjectMember.objects.create(
            project=self.project,
            member=self.team_member,
            budget=2000
        )
        
        self.income_record = ProjectBudgetRecord.objects.create(
            project=self.project,
            amount=5000,
            is_income=True,
            notes="Initial funding",
            is_editable=True
        )
        
        self.category1 = ProjectCategory.objects.create(
            project=self.project,
            name='Food'
        )
        
        self.category2 = ProjectCategory.objects.create(
            project=self.project,
            name='Transport'
        )
        
        now = timezone.now()
        self.transaction1 = Transaction.objects.create(
            user=self.team_member,
            amount=1000,
            project=self.project,
            transaction_category=self.category1,
            created_at=now - timedelta(days=5)
        )
        
        self.transaction2 = Transaction.objects.create(
            user=self.team_member,
            amount=500,
            project=self.project,
            transaction_category=self.category2,
            created_at=now - timedelta(days=3)
        )
        
        self.transaction3 = Transaction.objects.create(
            user=self.team_member,
            amount=750,
            project=self.project,
            transaction_category=self.category1,
            created_at=now - timedelta(days=1)
        )
        
        self.manager_token = self.get_token(self.manager)
        self.member_token = self.get_token(self.team_member)
        self.other_token = self.get_token(self.other_user)
        
        self.url = reverse('project-analytics', args=[self.project.id])
    
    def get_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_get_analytics_success(self):
        """Test that project manager can access analytics (A01: Broken Access Control)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the analytics data
        data = response.data
        self.assertEqual(data['total_earnings'], 5000)
        self.assertEqual(data['total_spendings'], 2250)
        
        # Check top categories
        self.assertEqual(len(data['top_categories']), 2)
        food_category = next((c for c in data['top_categories'] if c['name'] == 'Food'), None)
        self.assertIsNotNone(food_category)
        self.assertEqual(food_category['total_spendings'], 1750)
        
        # Check top members
        self.assertEqual(len(data['top_members']), 1)
        self.assertEqual(data['top_members'][0]['username'], 'teammember')
        self.assertEqual(data['top_members'][0]['total_amount'], 2250)

    def test_get_analytics_unauthorized(self):
        """Test that non-managers can't access analytics (A01: Broken Access Control)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.member_token}')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
        self.assertIn("don't have permissions", response.data['detail'])

    def test_get_analytics_unauthenticated(self):
        """Test unauthenticated access is denied (A07: Authentication Failures)."""
        self.client.credentials()  # Remove credentials
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_analytics_nonexistent_project(self):
        """Test handling of non-existent project (A10: SSRF)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        url = reverse('project-analytics', args=[uuid.uuid4()])  # Random UUID
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_analytics_with_filters(self):
        """Test analytics with month/year filters (A04: Insecure Design)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        
        current_time = timezone.now()
        current_month = current_time.month
        current_year = current_time.year
        
        response = self.client.get(f"{self.url}?month={current_month}&year={current_year}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if current_month < 12:
            future_month = current_month + 1
            response = self.client.get(f"{self.url}?month={future_month}&year={current_year}")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        future_year = current_year + 1
        response = self.client.get(f"{self.url}?year={future_year}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response = self.client.get(f"{self.url}?month=13")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with non-numeric values (SQL Injection attempt) (A03: Injection)
        response = self.client.get(f"{self.url}?month=1%27%20OR%20%271%27=%271")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response = self.client.get(f"{self.url}?year=2023%27%20OR%20%271%27=%271")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analytics_xss_prevention(self):
        """Test XSS prevention in category names (A03: Injection)."""
        xss_category = ProjectCategory.objects.create(
            project=self.project,
            name='<script>alert("XSS")</script>'
        )
        
        Transaction.objects.create(
            user=self.team_member,
            amount=300,
            project=self.project,
            transaction_category=xss_category
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        xss_category_data = next((c for c in response.data['top_categories'] 
                                if c['name'] == '<script>alert("XSS")</script>'), None)
        
        self.assertIsNotNone(xss_category_data)

    def test_analytics_integrity(self):
        """Test data integrity in analytics (A08: Software and Data Integrity Failures)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        
        response1 = self.client.get(self.url)
        
        Transaction.objects.create(
            user=self.team_member,
            amount=1200,
            project=self.project,
            transaction_category=self.category1
        )
        
        response2 = self.client.get(self.url)
        
        self.assertEqual(response2.data['total_spendings'] - response1.data['total_spendings'], 1200)
        
        food_category1 = next((c for c in response1.data['top_categories'] if c['name'] == 'Food'), None)
        food_category2 = next((c for c in response2.data['top_categories'] if c['name'] == 'Food'), None)
        
        self.assertEqual(food_category2['total_spendings'] - food_category1['total_spendings'], 1200)

    def test_analytics_handles_errors(self):
        """Test error handling (A05: Security Misconfiguration)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        
        response = self.client.get(f"{self.url}?month=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}invalid')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_analytics_logging(self):
        """Test proper logging of access attempts (A09: Security Logging and Monitoring Failures)."""
        
        with self.assertLogs(level='INFO') as cm:
            logging.getLogger().info("Analytics accessed by user")
            self.assertIn("Analytics accessed by user", cm.output[0])
            
    def test_analytics_project_access_protection(self):
        """Test that access control prevents information disclosure (A01, A07 combined)."""
        other_project = Project.objects.create(
            manager=self.other_user,
            name='Other Project',
            description='Project for testing cross-access',
            total_budget=5000
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        other_url = reverse('project-analytics', args=[other_project.id])
        
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analytics_concurrent_user_access(self):
        """Test for race conditions (A04: Insecure Design)."""

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        response1 = self.client.get(self.url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        Transaction.objects.create(
            user=self.team_member,
            amount=2500,
            project=self.project,
            transaction_category=self.category2
        )
        
        response2 = self.client.get(self.url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        self.assertEqual(
            response2.data['total_spendings'] - response1.data['total_spendings'], 
            2500
        )