import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import serializers
from django.utils import timezone
from authentication.models import WaletUser
from projects.models import Project, ProjectMember
from projects.serializers import ProjectMemberSerializer

class ProjectMemberSerializerTests(TestCase):
    def setUp(self):
        """Set up test data for ProjectMemberSerializer tests."""
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

        self.project_member = ProjectMember.objects.create(
            member=self.user,
            project=self.project,
            budget=1000
        )

        self.client = APIClient()

    def test_serialize_project_member(self):
        """Test that ProjectMemberSerializer correctly serializes a ProjectMember instance."""
        serializer = ProjectMemberSerializer(self.project_member)
        data = serializer.data

        self.assertEqual(data['id'], str(self.project_member.id))
        self.assertEqual(data['budget'], 1000)
        self.assertEqual(data['member_name'], self.user.username)
        self.assertTrue(data['created_at'])

    def test_deserialize_create_project_member(self):
        """Test that ProjectMemberSerializer can create a new ProjectMember."""
        data = {
            "member": str(self.admin.id),
            "project": str(self.project.id),
            "budget": 2000
        }
        serializer = ProjectMemberSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        project_member = serializer.save()

        self.assertEqual(project_member.member, self.admin)
        self.assertEqual(project_member.project, self.project)
        self.assertEqual(project_member.budget, 2000)

    def test_read_only_fields(self):
        """Test that read-only fields cannot be modified."""
        data = {
            "member": str(self.admin.id),
            "project": str(self.project.id),
            "budget": 1500,
            "id": str(uuid.uuid4()),  
            "created_at": timezone.now().isoformat(),
        }
        serializer = ProjectMemberSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        project_member = serializer.save()
        serialized_data = ProjectMemberSerializer(project_member).data

        self.assertNotEqual(project_member.id, uuid.UUID(data['id']))
        self.assertNotEqual(project_member.created_at.isoformat(), data['created_at'])


    def test_sensitive_data_exposure(self):
        """Test that sensitive data (e.g., password) is not exposed in serialized output."""
        serializer = ProjectMemberSerializer(self.project_member)
        data = serializer.data

        self.assertNotIn("password", data)
        self.assertEqual(data["budget"], 1000)