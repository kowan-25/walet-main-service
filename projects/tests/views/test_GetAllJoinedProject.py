from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from projects.models import Project, ProjectMember
from django.contrib.auth import get_user_model

User = get_user_model()
class GetAllJoinedProjectTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
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
        self.url = reverse('projects-joined-list')
    
    def authenticate(self, data):
        login_res = self.client.post(self.login_url, data, format='json')
        token = login_res.data.get("access")
        return {'Authorization': f'Bearer {token}'}
    
    def test_get_all_joined_projects_authenticated(self):
        """Test that authenticated users can get the list of projects they manage."""
        data = {
            "username": "otheruser",
            "password": "testpass"
        }

        headers = self.authenticate(data)
        response = self.client.get(self.url, headers=headers)  
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that the response contains the correct project data
        project_names = [project['name'] for project in response.data]

        self.assertIn('Project 1', project_names)

    def test_get_all_joined_projects_unauthenticated(self):
        """Test that unauthenticated users cannot access the managed projects."""
        response = self.client.get(self.url)  

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_joined_projects_no_projects(self):
        """Test that if a user join no projects, an empty list is returned."""
        data = {
            "username": "testuser",
            "password": "testpass"
        }

        headers = self.authenticate(data)
        response = self.client.get(self.url, headers=headers)  

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])  # No projects for 'otheruser'
