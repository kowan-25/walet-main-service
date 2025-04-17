from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from authentication.models import WaletUser
from projects.models import Project, ProjectInvitation, ProjectMember
from uuid import uuid4
from datetime import timedelta
import json

class AddTeamMemberTest(APITestCase):
    def setUp(self):
        self.manager = WaletUser.objects.create_user(
            username='projectmanager',
            password='secure_password123',
            email='manager@example.com'
        )
        self.manager.is_active = True
        self.manager.save()
        
        self.invitee = WaletUser.objects.create_user(
            username='teaminvitee',
            password='secure_password456',
            email='invitee@example.com'
        )
        self.invitee.is_active = True
        self.invitee.save()
        
        self.other_user = WaletUser.objects.create_user(
            username='otheruser',
            password='secure_password789',
            email='other@example.com'
        )
        self.other_user.is_active = True
        self.other_user.save()
        
        self.project = Project.objects.create(
            manager=self.manager,
            name='Test Project',
            description='A project for testing team member addition',
            total_budget=5000
        )
        
        self.invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee,
            expires_at=timezone.now() + timedelta(days=2)
        )
        
        self.expired_invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        self.used_invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee,
            is_used=True
        )
        
        self.other_invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.other_user
        )
        
        self.invitee_token = self.get_token(self.invitee)
        self.manager_token = self.get_token(self.manager)
        self.other_token = self.get_token(self.other_user)

    def get_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def get_url(self, token):
        return reverse('add-team-member', args=[token])

    def test_add_team_member_success(self):
        """Test successful team member addition with valid invitation (A01: Broken Access Control)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.invitee_token}')
        url = self.get_url(self.invitation.id)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(
            ProjectMember.objects.filter(project=self.project, member=self.invitee).exists()
        )
        
        invitation = ProjectInvitation.objects.get(id=self.invitation.id)
        self.assertTrue(invitation.is_used)

    def test_add_team_member_unauthenticated(self):
        """Test unauthenticated access is denied (A07: Identification and Authentication Failures)."""
        url = self.get_url(self.invitation.id)
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertFalse(
            ProjectMember.objects.filter(project=self.project, member=self.invitee).exists()
        )

    def test_add_team_member_wrong_user(self):
        """Test only invited user can accept invitation (A01: Broken Access Control)."""
        # Try accepting someone else's invitation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        url = self.get_url(self.invitation.id)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'this invitation is not for you')

        self.assertFalse(
            ProjectMember.objects.filter(project=self.project, member=self.invitee).exists()
        )

    def test_add_team_member_expired_invitation(self):
        """Test expired invitation handling (A02: Cryptographic Failures)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.invitee_token}')
        url = self.get_url(self.expired_invitation.id)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invitation Expired')
        
        self.assertFalse(
            ProjectMember.objects.filter(project=self.project, member=self.invitee).exists()
        )

    def test_add_team_member_already_used_invitation(self):
        """Test already used invitation handling (A01: Broken Access Control)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.invitee_token}')
        url = self.get_url(self.used_invitation.id)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invitation Already Used')
        
        # Verify member was not added
        self.assertFalse(
            ProjectMember.objects.filter(project=self.project, member=self.invitee).exists()
        )

    def test_add_team_member_nonexistent_invitation(self):
        """Test non-existent invitation handling (A10: SSRF)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.invitee_token}')
        url = self.get_url(uuid4())  # Random UUID that doesn't exist
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify member was not added
        self.assertFalse(
            ProjectMember.objects.filter(project=self.project, member=self.invitee).exists()
        )

    def test_add_team_member_sql_injection_attempt(self):
        """Test protection against SQL injection (A03: Injection)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.invitee_token}')
        
        # Attempt SQL injection in URL
        malicious_url = "/api/projects/add-member/1'; DROP TABLE projects_projectmember; --"
        response = self.client.post(malicious_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        member_count = ProjectMember.objects.count()
        self.assertEqual(member_count, 0)  # No members should be added yet

    def test_add_team_member_already_in_project(self):
        """Test preventing duplicate project membership (A04: Insecure Design)."""
        # First add the member normally
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.invitee_token}')
        url = self.get_url(self.invitation.id)
        self.client.post(url)
        
        # Create a new invitation for the same user/project
        new_invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee
        )
        
        # Try to add the same member again
        url = self.get_url(new_invitation.id)
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'User Already in Project')
        
        # Verify only one membership exists
        self.assertEqual(
            ProjectMember.objects.filter(project=self.project, member=self.invitee).count(),
            1
        )

    def test_add_team_member_marks_all_invitations_used(self):
        """Test that all invitations for this project/user are marked as used (A08: Software and Data Integrity)."""
        second_invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee
        )
        third_invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.invitee_token}')
        url = self.get_url(self.invitation.id)
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that all invitations were marked as used
        for invitation_id in [self.invitation.id, second_invitation.id, third_invitation.id]:
            invitation = ProjectInvitation.objects.get(id=invitation_id)
            self.assertTrue(invitation.is_used)
            
    def test_add_team_member_idempotent_token(self):
        """Test that token cannot be reused (A07: Identification and Authentication Failures)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.invitee_token}')
        url = self.get_url(self.invitation.id)
        
        # First attempt should succeed
        response1 = self.client.post(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second attempt with same token should fail
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response2.data['error'], 'Invitation Already Used')
        
        # Verify only one membership was created
        self.assertEqual(
            ProjectMember.objects.filter(project=self.project, member=self.invitee).count(),
            1
        )

    def test_add_team_member_invalid_token_format(self):
        """Test protection against malformed tokens (A05: Security Misconfiguration)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.invitee_token}')
        
        invalid_url = "/api/project/add-member/not-a-valid-uuid"
        response = self.client.post(invalid_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)