from django.test import TestCase
from django.db import IntegrityError
from projects.models import Project, ProjectCategory
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectCategoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        self.project = Project.objects.create(
            name="Test Project",
            description="Description here",
            manager=self.user,
            total_budget=1000
        )

    def test_create_project_category_success(self):
        category = ProjectCategory.objects.create(project=self.project, name="Category A")
        self.assertEqual(category.name, "Category A")
        self.assertEqual(str(category), "Category A Test Project")

    def test_unique_constraint_project_and_name(self):
        ProjectCategory.objects.create(project=self.project, name="UniqueCategory")
        with self.assertRaises(IntegrityError):
            ProjectCategory.objects.create(project=self.project, name="UniqueCategory")
