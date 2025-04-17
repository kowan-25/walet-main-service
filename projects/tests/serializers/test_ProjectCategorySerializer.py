from django.test import TestCase
from projects.models import Project, ProjectCategory
from projects.serializers import ProjectCategorySerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectCategorySerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        self.project = Project.objects.create(
            name="Test Project",
            description="Description here",
            manager=self.user,
            total_budget=1000
        )
        self.valid_data = {
            "project": str(self.project.id),
            "name": "Design"
        }

    def test_valid_serializer_creates_category(self):
        serializer = ProjectCategorySerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        category = serializer.save()
        self.assertEqual(category.name, self.valid_data["name"])
        self.assertEqual(category.project, self.project)


    def test_serializer_output(self):
        category = ProjectCategory.objects.create(project=self.project, name="Development")
        serializer = ProjectCategorySerializer(category)
        self.assertEqual(serializer.data["name"], "Development")
        self.assertEqual(str(serializer.data["project"]), str(self.project.id))
