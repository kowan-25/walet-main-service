from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectCategory

User = get_user_model()

class CreateProjectCategoryTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass", email='test@example.com')
        self.project = Project.objects.create(
            name="Test Project",
            description="Some description",
            manager=self.user,
            total_budget=1000
        )

        self.otheruser = User.objects.create_user(username="otheruser", password="testpass", email='othertest@example.com')
       
        # URL with UUID param
        self.url = reverse('create-project-category')  
        
    
    def test_create_projectcategory_success(self):
        self.client.force_authenticate(user=self.user)
        
        data = {
            "project_id": self.project.id,
            "name": "IT Dev"
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectCategory.objects.count(), 1)
        self.assertEqual(ProjectCategory.objects.first().name, 'IT Dev')

    def test_create_projectcategory_missing_field(self):
        self.client.force_authenticate(user=self.user)
        
        data = {
            "project_id": self.project.id
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
    
    def test_create_projectcategory_unauthenticated(self):
        data = {
            "project_id": self.project.id,
            "name": "IT Dev"
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_projectcategory_not_manager(self):
        self.client.force_authenticate(user=self.otheruser)

        data = {
            "project_id": self.project.id,
            "name": "IT Dev"
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "You don't have permissions to add category to this Project")



