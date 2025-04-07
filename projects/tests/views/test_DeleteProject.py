from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from projects.models import Project

User = get_user_model()

class CreateProjectTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass", email='test@example.com')
        self.user.is_active = True
        self.user.save()

        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass',
            email='other@example.com',
        )
        self.other_user.is_active = True
        self.other_user.save()

        self.project = Project.objects.create(
            name="Project 1",
            description="Test project 1",
            manager=self.user,
            total_budget=1000
        )

        self.login_url = reverse('login')
        self.url = reverse('delete-project', kwargs={'pk': str(self.project.id)})


    def authenticate(self, data):
        login_res = self.client.post(self.login_url, data, format='json')
        token = login_res.data.get("access")
        return {'Authorization': f'Bearer {token}'}
    
    def test_delete_project_success(self):
        login_data = {
            "username": "testuser",
            "password": "testpass"
        }

        headers = self.authenticate(login_data)
        response = self.client.delete(self.url, format='json', headers=headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data['message'], "Project deleted successfully")

    
    def test_delete_project_unauthenticated(self):
       
        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_project_not_manager(self):
        login_data = {
            "username": "otheruser",
            "password": "testpass"
        }

        headers = self.authenticate(login_data)
        response = self.client.delete(self.url, format='json', headers=headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data['detail'], "You don't have permissions to delete this project")



