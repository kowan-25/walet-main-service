from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectCategory

User = get_user_model()

class DeleteProjectCategoryTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass", email='test@example.com')
        self.otheruser = User.objects.create_user(username='otheruser', password='testpass', email='other@example.com')
       
        self.project = Project.objects.create(
            name="Project 1",
            description="Test project 1",
            manager=self.user,
            total_budget=1000
        )
        
        self.category = ProjectCategory.objects.create(project=self.project, name="Design")

        self.url = reverse('delete-project-category', kwargs={'pk': str(self.category.id)})
    
    def test_delete_project_success(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data['message'], "category deleted successfully")

    
    def test_delete_project_unauthenticated(self):

        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_project_not_manager(self):
        self.client.force_authenticate(user=self.otheruser)

        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data['detail'], "You don't have permissions to delete category to this Project")



