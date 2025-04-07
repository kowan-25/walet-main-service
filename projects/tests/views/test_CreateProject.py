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
        
        self.login_url = reverse('login')  # Replace with actual login URL name
        self.create_url = reverse('create-project')  # Replace with actual URL name


    def authenticate(self, data):
        login_res = self.client.post(self.login_url, data, format='json')
        token = login_res.data.get("access")
        return {'Authorization': f'Bearer {token}'}
    
    def test_create_project_success(self):
        login_data = {
            "username": "testuser",
            "password": "testpass"
        }

        data = {
            "name": "Test Project",
            "description": "This is a test"
        }

        headers = self.authenticate(login_data)
        response = self.client.post(self.create_url, data, format='json', headers=headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Test Project")
        self.assertTrue(Project.objects.filter(name="Test Project", manager=self.user).exists())

    def test_create_project_missing_name(self):
        login_data = {
            "username": "testuser",
            "password": "testpass"
        }
         
        data = {
            "description": "Missing name"
        }

        headers = self.authenticate(login_data)
        response = self.client.post(self.create_url, data, format='json', headers=headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
    
    def test_create_project_unauthenticated(self):
        data = {
            "name": "Test Project",
            "description": "Missing name"
        }

        response = self.client.post(self.create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


