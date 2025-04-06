from django.test import TestCase
from django.core.exceptions import ValidationError
from authentication.models import WaletUser
from projects.models import Project
from uuid import UUID


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = WaletUser.objects.create(
            username='manageruser',
            password='testpassword123',
            email='manager@example.com',
            is_active=True
        )

    def test_create_valid_project(self):
        """Test creating a valid project instance."""
        project = Project.objects.create(
            manager=self.user,
            name='Test Project',
            description='This is a test project.',
            total_budget=1000,
            status=True
        )

        self.assertIsInstance(project.id, UUID)
        self.assertEqual(project.manager, self.user)
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.description, 'This is a test project.')
        self.assertEqual(project.total_budget, 1000)
        self.assertTrue(project.status)
        self.assertIsNotNone(project.created_at)
        self.assertIsNotNone(project.updated_at)

    def test_negative_budget_raises_validation_error(self):
        """Test that a negative budget raises ValidationError."""
        project = Project(
            manager=self.user,
            name='Negative Budget Project',
            total_budget=-100
        )
        with self.assertRaises(ValidationError):
            project.full_clean() 

    def test_blank_optional_fields(self):
        """Test that optional fields (description) can be blank/null."""
        project = Project.objects.create(
            manager=self.user,
            name='No Description Project',
            total_budget=500
        )

        self.assertEqual(project.description, None)
        self.assertFalse(project.status)
        self.assertEqual(project.total_budget, 500)

    def test_default_status_and_budget(self):
        """Test that default values for status and budget are set properly."""
        project = Project.objects.create(
            manager=self.user,
            name='Default Value Project'
        )

        self.assertFalse(project.status)
        self.assertEqual(project.total_budget, 0)

    def test_str_representation(self):
        """Test string representation returns the project name."""
        project = Project.objects.create(
            manager=self.user,
            name='Visible Project Name'
        )

        self.assertEqual(str(project), 'Visible Project Name')
