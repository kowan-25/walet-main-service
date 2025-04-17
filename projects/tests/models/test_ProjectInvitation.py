from django.test import TestCase
from django.utils import timezone
from authentication.models import WaletUser
from projects.models import Project, ProjectInvitation
from uuid import UUID, uuid4
from datetime import timedelta


class ProjectInvitationModelTest(TestCase):
    def setUp(self):
        self.manager = WaletUser.objects.create(
            username='manageruser',
            password='testpassword123',
            email='manager@example.com',
            is_active=True
        )
        
        self.invitee = WaletUser.objects.create(
            username='invitee',
            password='secure_password456',
            email='invitee@example.com',
            is_active=True
        )
        
        self.project = Project.objects.create(
            manager=self.manager,
            name='Test Project',
            description='This is a test project.',
            total_budget=1000,
            status=True
        )

    def test_create_valid_invitation(self):
        """Test creating a valid project invitation instance."""
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee
        )

        self.assertIsInstance(invitation.id, UUID)
        self.assertEqual(invitation.project, self.project)
        self.assertEqual(invitation.user, self.invitee)
        self.assertFalse(invitation.is_used)
        self.assertIsNotNone(invitation.created_at)
        self.assertIsNotNone(invitation.expires_at)
        
        # Verify expiration is roughly 3 days from now
        expected_expiry = timezone.now() + timedelta(days=3)
        difference = expected_expiry - invitation.expires_at
        self.assertLess(abs(difference.total_seconds()), 10)  # Allow for a small difference due to test execution time

    def test_str_representation(self):
        """Test string representation is formatted correctly."""
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee
        )
        expected_str = f"Invitation for {self.invitee.username} to join {self.project.name}"
        self.assertEqual(str(invitation), expected_str)

    def test_expired_invitation(self):
        """Test creation and validation of expired invitations."""
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee,
            expires_at=timezone.now() - timedelta(days=1)  # Set to expired
        )
        
        self.assertTrue(invitation.expires_at < timezone.now())

    def test_used_invitation(self):
        """Test creating an invitation that has been marked as used."""
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee,
            is_used=True
        )
        
        self.assertTrue(invitation.is_used)

    def test_default_fields(self):
        """Test that default values for is_used and expires_at are set properly."""
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee
        )
        
        self.assertFalse(invitation.is_used)
        self.assertIsNotNone(invitation.expires_at)
        
        # Check expires_at is approximately 3 days from creation date
        now = timezone.now()
        expected_expiry = now + timedelta(days=3)
        self.assertLess(abs((invitation.expires_at - expected_expiry).total_seconds()), 10)

    def test_invitation_cascade_on_delete(self):
        """Test invitation is deleted when project is deleted."""
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee
        )
        
        invitation_id = invitation.id
        self.project.delete()
        
        # The invitation should be deleted due to CASCADE relationship
        with self.assertRaises(ProjectInvitation.DoesNotExist):
            ProjectInvitation.objects.get(id=invitation_id)
            
    def test_invitation_user_cascade_on_delete(self):
        """Test invitation is deleted when user is deleted."""
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee
        )
        
        invitation_id = invitation.id
        self.invitee.delete()
        
        # The invitation should be deleted due to CASCADE relationship
        with self.assertRaises(ProjectInvitation.DoesNotExist):
            ProjectInvitation.objects.get(id=invitation_id)
    
    def test_custom_expiry_date(self):
        """Test creating an invitation with custom expiration date."""
        custom_expiry = timezone.now() + timedelta(days=7)
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.invitee,
            expires_at=custom_expiry
        )
        
        self.assertEqual(invitation.expires_at, custom_expiry)