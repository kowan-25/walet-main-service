from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from authentication.models import WaletUser
from projects.models import Project, ProjectInvitation
from uuid import uuid4
from datetime import timedelta
import json

class GetProjectInvitationsTest(APITestCase):
    def setUp(self):
        self.user1 = WaletUser.objects.create_user(
            username='testuser1',
            password='secure_password123',
            email='user1@example.com'
        )
        self.user1.is_active = True
        self.user1.save()

        self.user2 = WaletUser.objects.create_user(
            username='testuser2',
            password='secure_password456', 
            email='user2@example.com'
        )
        self.user2.is_active = True
        self.user2.save()
        
        self.manager = WaletUser.objects.create_user(
            username='manager',
            password='manager_password789',
            email='manager@example.com'
        )
        self.manager.is_active = True
        self.manager.save()
        
        self.project1 = Project.objects.create(
            manager=self.manager,
            name='Project One',
            description='First test project',
            total_budget=10000
        )
        
        self.project2 = Project.objects.create(
            manager=self.manager,
            name='Project Two',
            description='Second test project',
            total_budget=20000
        )
        
        self.valid_invitation1 = ProjectInvitation.objects.create(
            project=self.project1,
            user=self.user1,
            is_used=False,
            expires_at=timezone.now() + timedelta(days=2)
        )
        
        self.valid_invitation2 = ProjectInvitation.objects.create(
            project=self.project2,
            user=self.user1,
            is_used=False,
            expires_at=timezone.now() + timedelta(days=2)
        )
        
        self.expired_invitation = ProjectInvitation.objects.create(
            project=self.project1,
            user=self.user1,
            is_used=False,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        # Create used invitation
        self.used_invitation = ProjectInvitation.objects.create(
            project=self.project2,
            user=self.user1,
            is_used=True,
            expires_at=timezone.now() + timedelta(days=2)
        )
        
        # Create invitation for user2
        self.other_user_invitation = ProjectInvitation.objects.create(
            project=self.project1,
            user=self.user2,
            is_used=False,
            expires_at=timezone.now() + timedelta(days=2)
        )
        
        self.token1 = self.get_user_token(self.user1)
        self.token2 = self.get_user_token(self.user2)
        
        self.url = reverse('project-invitations-list')

    def get_user_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_get_invitations_authenticated(self):
        """Test authenticated user can retrieve their valid invitations (A01: Broken Access Control)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        project_ids = [invitation['project'] for invitation in response.data]
        self.assertIn(self.project1.id, project_ids)
        self.assertIn(self.project2.id, project_ids)

    def test_get_invitations_unauthenticated(self):
        """Test unauthenticated access is denied (A07: Identification and Authentication Failures)."""
        self.client.credentials()
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_invitations_expired_not_returned(self):
        """Test expired invitations are not returned (A02: Cryptographic Failures - expiry enforcement)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(self.url)
        
        invitation_ids = [invitation['id'] for invitation in response.data]
        self.assertNotIn(str(self.expired_invitation.id), invitation_ids)

    def test_get_invitations_used_not_returned(self):
        """Test used invitations are not returned (A01: Broken Access Control)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(self.url)
        
        invitation_ids = [invitation['id'] for invitation in response.data]
        self.assertNotIn(str(self.used_invitation.id), invitation_ids)

    def test_get_invitations_different_user(self):
        """Test users can only see their own invitations (A01: Broken Access Control)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token2}')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # User2 should only see their invitation
        invitation_id = response.data[0]['id']
        self.assertEqual(invitation_id, str(self.other_user_invitation.id))

    def test_get_invitations_invalid_token(self):
        """Test invalid authentication token is rejected (A07: Identification and Authentication Failures)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer invalid_token')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_invitations_content_type_json(self):
        """Test proper Content-Type headers are enforced (A05: Security Misconfiguration)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(
            self.url,
            HTTP_ACCEPT='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_get_invitations_no_sql_injection(self):
        """Test SQL injection protections (A03: Injection)."""
        # Try to inject SQL through URL manipulation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        malformed_url = '/api/invitations/1%3BDELETE%20FROM%20auth_user%3B'
        
        response = self.client.get(malformed_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_invitations_xss_project_name(self):
        """Test XSS prevention in project names (A03: Injection)."""
        xss_project = Project.objects.create(
            manager=self.manager,
            name='<script>alert("XSS")</script>',
            description='Project with XSS attempt',
            total_budget=5000
        )
        
        xss_invitation = ProjectInvitation.objects.create(
            project=xss_project,
            user=self.user1,
            is_used=False,
            expires_at=timezone.now() + timedelta(days=2)
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(self.url)
        
        # The API should return the project name with the script tags (as text)
        # but a proper frontend would encode this
        found_invitation = False
        for invitation in response.data:
            if invitation['id'] == str(xss_invitation.id):
                self.assertEqual(invitation['project_name'], '<script>alert("XSS")</script>')
                found_invitation = True
                break
                
        self.assertTrue(found_invitation, "XSS invitation not found in response")
        
    def test_no_sensitive_data_exposure(self):
        """Test no sensitive data is exposed in responses (A02: Cryptographic Failures)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(self.url)
        
        for invitation in response.data:
            # Verify that no sensitive internal data is leaked
            self.assertNotIn('is_used', invitation)  # This field exists in model but shouldn't be exposed
            
            # Check that only expected fields are present
            expected_fields = {'id', 'project', 'project_name', 'project_manager_username', 'user', 'created_at', 'expires_at'}
            self.assertTrue(set(invitation.keys()).issubset(expected_fields))