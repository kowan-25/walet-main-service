from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
import uuid

from authentication.models import WaletUser
from projects.models import Project, ProjectMember

class RemoveTeamMemberAPITestCase(TestCase):
    """Test suite for the RemoveTeamMember API view"""

    def setUp(self):
        """Set up test data"""
        self.manager = WaletUser.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="Password123!",
        )
        
        self.member = WaletUser.objects.create_user(
            username="teammember",
            email="member@example.com",
            password="Password123!",
        )
        
        self.other_user = WaletUser.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="Password123!",
        )
        
        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            manager=self.manager,
            total_budget=Decimal('1000.00')
        )
        
        self.project_member = ProjectMember.objects.create(
            project=self.project,
            member=self.member,
            budget=Decimal('200.00')
        )
        
        self.client = APIClient()
        
        self.url = reverse(
            "remove-team-member", 
            kwargs={
                "project_pk": self.project.pk,
                "member_pk": self.member.pk
            }
        )

    def test_remove_team_member_success(self):
        """Test successful removal of team member by project manager"""
        self.client.force_authenticate(user=self.manager)
        
        initial_budget = self.project.total_budget
        
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        with self.assertRaises(ProjectMember.DoesNotExist):
            ProjectMember.objects.get(
                project=self.project, 
                member=self.member
            )
        
        self.project.refresh_from_db()
        expected_budget = initial_budget + Decimal('200.00')
        self.assertEqual(self.project.total_budget, expected_budget)

    def test_remove_team_member_unauthorized(self):
        """Test removal attempt without authentication"""
        self.client.force_authenticate(user=None)
        
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.assertTrue(
            ProjectMember.objects.filter(
                project=self.project, 
                member=self.member
            ).exists()
        )

    def test_remove_team_member_wrong_user(self):
        """Test removal attempt by user who is not the project manager"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        self.assertTrue(
            ProjectMember.objects.filter(
                project=self.project, 
                member=self.member
            ).exists()
        )

    def test_remove_nonexistent_team_member(self):
        """Test removing a team member that doesn't exist"""
        self.client.force_authenticate(user=self.manager)
        
        non_existent_pk = "123e4567-e89b-12d3-a456-426614174000"  

        url = reverse(
            "remove-team-member", 
            kwargs={
                "project_pk": self.project.pk, 
                "member_pk": non_existent_pk
            }
        ) 
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_team_member_from_nonexistent_project(self):
        """Test removing a team member from a non-existent project"""
        self.client.force_authenticate(user=self.manager)
        
        non_existent_pk = "123e4567-e89b-12d3-a456-426614174000"  
        url = reverse(
            "remove-team-member", 
            kwargs={
                "project_pk": non_existent_pk, 
                "member_pk": self.member.pk
            }
        )  
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_non_member_from_project(self):
        """Test removing a user who is not a member of the project"""

        self.client.force_authenticate(user=self.manager)
        

        url = reverse(
            "remove-team-member", 
            kwargs={
                "project_pk": self.project.pk, 
                "member_pk": self.other_user.pk
            }
        )
        

        response = self.client.delete(url)
        

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_sql_injection_resistance(self):
        """Test resistance to SQL injection in URL parameters"""

        self.client.force_authenticate(user=self.manager)

        malicious_urls = [
            f"/api/projects/1;DROP TABLE project_members/members/1",
            f"/api/projects/1' OR '1'='1/members/1",
            f"/api/projects/1/members/1' OR '1'='1"
        ]
        
        for url in malicious_urls:
            response = self.client.delete(url)
            self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])
            
            self.assertTrue(
                ProjectMember.objects.filter(
                    project=self.project, 
                    member=self.member
                ).exists()
            )

    def test_transaction_rollback(self):
        """Test that the transaction rolls back if an error occurs"""
        self.client.force_authenticate(user=self.manager)

        original_budget = self.project.total_budget
        
        original_delete = ProjectMember.delete
        
        try:
            def mock_delete(self, *args, **kwargs):
                raise RuntimeError("Simulated failure during deletion")
            
            ProjectMember.delete = mock_delete
            
            with transaction.atomic():
                try:
                    response = self.client.delete(self.url)
                except RuntimeError:
                    pass

            self.project.refresh_from_db()
            self.assertEqual(self.project.total_budget, original_budget)
            
            self.assertTrue(
                ProjectMember.objects.filter(
                    project=self.project, 
                    member=self.member
                ).exists()
            )
        
        finally:
            ProjectMember.delete = original_delete

    def test_race_condition_resistance(self):
        """Test resistance to race conditions when multiple requests try to remove same member"""
        self.client.force_authenticate(user=self.manager)
        
        response1 = self.client.delete(self.url)
        self.assertEqual(response1.status_code, status.HTTP_204_NO_CONTENT)
        
        response2 = self.client.delete(self.url)
        self.assertEqual(response2.status_code, status.HTTP_404_NOT_FOUND)
        
        self.project.refresh_from_db()
        expected_budget = Decimal('1000.00') + Decimal('200.00') 
        self.assertEqual(self.project.total_budget, expected_budget)