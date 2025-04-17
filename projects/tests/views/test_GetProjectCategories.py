from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectCategory
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

User = get_user_model()

class GetProjectCategoriesTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass", email='test@example.com')
        self.project = Project.objects.create(
            name="Test Project",
            description="Some description",
            manager=self.user,
            total_budget=1000
        )
        self.category1 = ProjectCategory.objects.create(project=self.project, name="Design")
        self.category2 = ProjectCategory.objects.create(project=self.project, name="Development")

        # URL with UUID param
        self.url = reverse('project-categories-list', kwargs={'project_id': str(self.project.id)})  
    
    
    def test_get_project_categories_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        category_names = [cat['name'] for cat in response.data]
        self.assertIn("Design", category_names)
        self.assertIn("Development", category_names)

    def test_get_project_categories_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
