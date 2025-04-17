from django.test import TestCase
from django.utils import timezone
from authentication.models import WaletUser
from projects.models import Project, ProjectInvitation
from projects.serializers import ProjectInvitationSerializer
from datetime import timedelta
from uuid import uuid4


class ProjectInvitationSerializerTest(TestCase):
    def setUp(self):
        self.manager = WaletUser.objects.create_user(
            username="manager", 
            password="managerpass", 
            email="manager@example.com"
        )
        
        self.invitee = WaletUser.objects.create_user(
            username="invitee", 
            password="inviteepass", 
            email="invitee@example.com"
        )
        
        self.project = Project.objects.create(
            manager=self.manager,
            name="Test Project",
            description="A test project"
        )
        
        self.invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee
        )

    def test_invitation_serializer_valid_data(self):
        """Test ProjectInvitationSerializer with valid input data."""
        data = {
            "project": self.project.id,
            "user": self.invitee.id,
        }
        serializer = ProjectInvitationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Check required fields are properly validated
        validated_data = serializer.validated_data
        self.assertEqual(validated_data["project"].id, self.project.id)
        self.assertEqual(validated_data["user"].id, self.invitee.id)

    def test_invitation_serializer_rejects_read_only_fields(self):
        """Test that read-only fields cannot be manually set."""
        custom_date = timezone.now() + timedelta(days=10)
        data = {
            "project": self.project.id,
            "user": self.invitee.id,
            "id": str(uuid4()),  # read_only
            "created_at": "2025-01-01T00:00:00Z",  # read_only
            "expires_at": custom_date.isoformat(),  # read_only
            "is_used": True  # read_only
        }
        serializer = ProjectInvitationSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # Still valid, read-only fields are ignored
        
        validated = serializer.validated_data
        self.assertNotIn("id", validated)
        self.assertNotIn("created_at", validated)
        self.assertNotIn("expires_at", validated)
        self.assertNotIn("is_used", validated)

    def test_invitation_serializer_missing_required_fields(self):
        """Test that serializer fails when required fields are missing."""
        # Missing both required fields
        data = {}
        serializer = ProjectInvitationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("project", serializer.errors)
        self.assertIn("user", serializer.errors)
        
        # Missing user field
        data = {"project": self.project.id}
        serializer = ProjectInvitationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user", serializer.errors)
        
        # Missing project field
        data = {"user": self.invitee.id}
        serializer = ProjectInvitationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("project", serializer.errors)

    def test_invitation_serializer_invalid_ids(self):
        """Test that serializer fails with non-existent IDs."""
        # Non-existent project ID
        data = {
            "project": str(uuid4()),  # Random non-existent ID
            "user": self.invitee.id
        }
        serializer = ProjectInvitationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("project", serializer.errors)
        
        # Non-existent user ID
        data = {
            "project": self.project.id,
            "user": str(uuid4())  # Random non-existent ID
        }
        serializer = ProjectInvitationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user", serializer.errors)

    def test_invitation_serializer_serialization(self):
        """Test serializing an existing invitation object."""
        serializer = ProjectInvitationSerializer(self.invitation)
        data = serializer.data
        
        self.assertEqual(data["project"], self.project.id)
        self.assertEqual(data["user"], self.invitee.id)
        self.assertFalse(data["is_used"])
        self.assertIn("created_at", data)
        self.assertIn("expires_at", data)
        self.assertIn("id", data)

    def test_invitation_serializer_update(self):
        """Test updating an invitation via the serializer."""
        new_user = WaletUser.objects.create_user(
            username="newuser", 
            password="newpass", 
            email="new@example.com"
        )
        
        data = {
            "project": self.project.id,
            "user": new_user.id,
            "is_used": True  # This should be ignored as it's read-only
        }
        
        serializer = ProjectInvitationSerializer(self.invitation, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_invitation = serializer.save()
        
        # The user should be updated, but is_used should remain unchanged
        self.assertEqual(updated_invitation.user, new_user)
        self.assertEqual(updated_invitation.project, self.project)
        self.assertFalse(updated_invitation.is_used)  # Should still be False despite trying to set it to True