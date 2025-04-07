from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from projects.models import Project, ProjectMember
from django.contrib.auth import get_user_model

User = get_user_model()
class GetProjectByidTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='manageruser',
            password='testpass',
            email='test@example.com'
        )
        self.user.is_active = True
        self.user.save()

        # Create another user (to test the authorization)
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass',
            email='other@example.com',
        )
        self.other_user.is_active = True
        self.other_user.save()

        # Create projects for the test user and another user
        self.project1 = Project.objects.create(
            name="Project 1",
            description="Test project 1",
            manager=self.user,
            total_budget=1000
        )
        self.project2 = Project.objects.create(
            name="Project 2",
            description="Test project 2",
            manager=self.user,
            total_budget=2000
        )

        self.projectmember1 = ProjectMember.objects.create(
            member=self.other_user,
            project=self.project1
        )

        # Set up the API client
        self.client = APIClient()
        self.client.login(username='testuser', password='testpass')  # Authenticate as 'testuser'
        self.login_url = reverse('login')
    
    def authenticate(self, data):
        login_res = self.client.post(self.login_url, data, format='json')
        token = login_res.data.get("access")
        return {'Authorization': f'Bearer {token}'}
    
    def test_manager_can_view_project(self):
        """Test that manager can access the managed projects."""
        data = {
            "username": "manageruser",
            "password": "testpass"
        }

        headers = self.authenticate(data)
        res = self.client.get(reverse('project-detail', kwargs={'pk': str(self.project1.id)}), headers=headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], str(self.project1.id))

    def test_team_member_can_view_project(self):
        """Test that member can access the managed projects."""
        data = {
            "username": "otheruser",
            "password": "testpass"
        }

        headers = self.authenticate(data)
        res = self.client.get(reverse('project-detail', kwargs={'pk': str(self.project1.id)}), headers=headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], str(self.project1.id))

    def test_stranger_cannot_view_project(self):
        """Test that non manager nor member cannot access the managed projects."""
        data = {
            "username": "otheruser",
            "password": "testpass"
        }

        headers = self.authenticate(data)
        res = self.client.get(reverse('project-detail', kwargs={'pk': str(self.project2.id)}), headers=headers)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("permissions", res.data['detail'].lower())