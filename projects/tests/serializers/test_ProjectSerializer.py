from django.test import TestCase
from authentication.models import WaletUser
from projects.models import Project
from projects.serializers import ProjectSerializer
from rest_framework.exceptions import ValidationError
from uuid import uuid4


class ProjectSerializerTest(TestCase):
    def setUp(self):
        self.user = WaletUser.objects.create_user(username="testuser", password="testpass", email="test@example.com")

    def test_project_serializer_valid_data(self):
        """Test ProjectSerializer with valid input data."""
        data = {
            "name": "Test Project",
            "description": "A test project",
        }
        serializer = ProjectSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_project_serializer_rejects_read_only_fields(self):
        """Test that read-only fields cannot be manually set."""
        data = {
            "name": "Invalid Project",
            "total_budget": 10000,  # read_only
            "manager": self.user.id,  # read_only
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "id": str(uuid4())
        }
        serializer = ProjectSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # Still valid, read-only fields are ignored
        validated = serializer.validated_data
        self.assertNotIn("manager", validated)
        self.assertNotIn("created_at", validated)
        self.assertNotIn("total_budget", validated)

    def test_project_serializer_missing_required_fields(self):
        """Test that serializer fails when required fields are missing."""
        data = {}
        serializer = ProjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_project_serializer_blank_description(self):
        """Test that description can be blank."""
        data = {
            "name": "Project with Blank Description",
            "description": ""
        }
        serializer = ProjectSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    
        

