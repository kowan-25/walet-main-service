from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from unittest.mock import patch, MagicMock
from authentication.models import WaletUser
from projects.models import Project, ProjectInvitation, ProjectMember
from uuid import uuid4
import json
import os

class InviteTeamMemberTest(APITestCase):
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
            description='A project for testing invitations',
            total_budget=5000
        )
        
        self.manager_token = self.get_token(self.manager)
        self.invitee_token = self.get_token(self.invitee)
        self.other_token = self.get_token(self.other_user)
        
        self.url = reverse('invite-team-member')
        
        self.valid_payload = {
            'project_id': str(self.project.id),
            'email': self.invitee.email
        }

    def get_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    @patch('requests.post')
    def test_invite_team_member_success(self, mock_post):
        """Test successful invitation by project manager (addresses A01: Broken Access Control)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Invitation sent')
        self.assertIn('token', response.data)
        
        # Verify invitation was created in the database
        invitation_id = response.data['token']
        invitation = ProjectInvitation.objects.get(id=invitation_id)
        self.assertEqual(invitation.project, self.project)
        self.assertEqual(invitation.user, self.invitee)
        self.assertFalse(invitation.is_used)
        
        # Verify the email service was called with correct data
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        self.assertIn('json', call_args)
        email_payload = call_args['json']
        self.assertEqual(email_payload['to'], self.invitee.email)
        self.assertEqual(email_payload['context']['name'], self.invitee.username)
        self.assertEqual(email_payload['context']['project_name'], self.project.name)

    def test_invite_team_member_unauthenticated(self):
        """Test unauthenticated access is denied (addresses A07: Authentication Failures)."""
        # No authentication credentials
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invite_team_member_non_manager(self):
        """Test non-manager cannot invite members (addresses A01: Broken Access Control)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
        self.assertIn("don't have permissions", response.data['detail'])

    def test_invite_team_member_missing_fields(self):
        """Test validation of required fields (addresses A04: Insecure Design)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        
        empty_payload = {}
        response = self.client.post(
            self.url,
            data=json.dumps(empty_payload),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        null_payload = {
            'project_id': None,
            'email': None
        }
        response = self.client.post(
            self.url,
            data=json.dumps(null_payload),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        empty_string_payload = {
            'project_id': '',
            'email': ''
        }
        response = self.client.post(
            self.url,
            data=json.dumps(empty_string_payload),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_team_member_nonexistent_project(self):
        """Test handling of non-existent project (addresses A10: SSRF)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        
        invalid_payload = {
            'project_id': str(uuid4()),  # Random non-existent project ID
            'email': self.invitee.email
        }
        response = self.client.post(
            self.url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_team_member_nonexistent_user(self):
        """Test handling of non-existent user email (addresses A10: SSRF)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        
        invalid_payload = {
            'project_id': str(self.project.id),
            'email': 'nonexistent@example.com'  # Email that doesn't exist
        }
        response = self.client.post(
            self.url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_team_member_self_invitation(self):
        """Test prevention of self-invitation (addresses A04: Insecure Design)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        
        invalid_payload = {
            'project_id': str(self.project.id),
            'email': self.manager.email
        }
        response = self.client.post(
            self.url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'You Cannot Invite Yourself')

    @patch('requests.post')
    def test_invite_team_member_already_in_project(self, mock_post):
        """Test prevention of duplicate invitations (addresses A01: Broken Access Control)."""
        ProjectMember.objects.create(
            project=self.project,
            member=self.invitee
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'User Already in Project')
        
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_invite_team_member_email_failure(self, mock_post):
        """Test handling of email service failure (addresses A05: Security Misconfiguration)."""
        from requests.exceptions import RequestException
        mock_post.side_effect = RequestException("Email service error")
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Failed to send email')

    def test_invite_team_member_sql_injection(self):
        """Test protection against SQL injection (addresses A03: Injection)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.manager_token}')
        
        # Attempt SQL injection in the project_id
        sql_injection_payload = {
            'project_id': "'; DROP TABLE projects_projectinvitation; --",
            'email': self.invitee.email
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(sql_injection_payload),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])
        
        # Verify that the table still exists (no SQL injection happened)
        invitation_count = ProjectInvitation.objects.count()
        self.assertIsNotNone(invitation_count)