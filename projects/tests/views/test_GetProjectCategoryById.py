from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectCategory
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

User = get_user_model()

class GetProjectCategoryByIdTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass", email='test@example.com')
        self.project = Project.objects.create(
            name="Test Project",
            description="Some description",
            manager=self.user,
            total_budget=1000
        )
        self.category = ProjectCategory.objects.create(project=self.project, name="Design")

        # URL with UUID param
        self.url = reverse('project-category-detail', kwargs={'pk': str(self.category.id)})  
    
    
    def test_get_project_category_by_id_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Design", response.data["name"])

    def test_get_project_category_by_id_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_project_category_by_id_not_found(self):
        self.client.force_authenticate(user=self.user)
        invalid_url = reverse('project-category-detail', kwargs={"pk": "00000000-0000-0000-0000-000000000000"})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
