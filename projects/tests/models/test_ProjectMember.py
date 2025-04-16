import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone
from datetime import timedelta
from authentication.models import WaletUser
from projects.models import Project, ProjectMember

class ProjectMemberTests(TestCase):
    def setUp(self):
        """Set up test data for ProjectMember tests."""
        # Create WaletUser instances
        self.user = WaletUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123"
        )
        self.admin = WaletUser.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="A test project",
            manager_id=self.admin.id
        )

        # Create ProjectMember instance
        self.project_member = ProjectMember.objects.create(
            member=self.user,
            project=self.project,
            budget=1000
        )

    # Model Functionality Tests
    def test_project_member_creation(self):
        """Test that a ProjectMember is created correctly."""
        self.assertEqual(self.project_member.member, self.user)
        self.assertEqual(self.project_member.project, self.project)
        self.assertEqual(self.project_member.budget, 1000)
        self.assertTrue(self.project_member.created_at)
        self.assertIsInstance(self.project_member.id, uuid.UUID)

    def test_project_member_str(self):
        """Test the string representation of ProjectMember."""
        expected_str = f"{self.user.username} in Project {self.project.name}"
        self.assertEqual(str(self.project_member), expected_str)

    def test_unique_constraint(self):
        """Test that the unique constraint on project_id and member_id is enforced."""
        with self.assertRaises(IntegrityError):
            ProjectMember.objects.create(
                member=self.user,
                project=self.project,
                budget=2000
            )

    def test_foreign_key_cascade_member(self):
        """Test that deleting a member deletes associated ProjectMember instances."""
        member_id = self.user.id
        self.user.delete()
        self.assertFalse(ProjectMember.objects.filter(member_id=member_id).exists())

    def test_foreign_key_cascade_project(self):
        """Test that deleting a project deletes associated ProjectMember instances."""
        project_id = self.project.id
        self.project.delete()
        self.assertFalse(ProjectMember.objects.filter(project_id=project_id).exists())

    def test_budget_non_negative(self):
        """Test that budget cannot be negative."""
        project_member = ProjectMember(
            member=self.user,
            project=self.project,
            budget=-100
        )
        with self.assertRaises(ValidationError):
            project_member.full_clean()

    def test_sensitive_data_exposure(self):
        """Test that sensitive data (e.g., password) is not exposed in string representation."""
        self.assertNotIn(self.user.password, str(self.project_member))
        self.assertIn(self.user.username, str(self.project_member))
        self.assertIn(self.project.name, str(self.project_member))

    def test_required_fields(self):
        """Test that required fields cannot be omitted."""
        project_member = ProjectMember(
            budget=500
        )
        with self.assertRaises(ValidationError):
            project_member.full_clean()