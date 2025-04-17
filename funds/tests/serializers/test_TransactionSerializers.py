from django.test import TestCase
from authentication.models import WaletUser
from projects.models import Project, ProjectCategory
from funds.serializers import TransactionSerializer
from funds.models import Transaction
from rest_framework.exceptions import ValidationError
from uuid import uuid4

class TransactionSerializerTest(TestCase):
    def setUp(self):
        self.user = WaletUser.objects.create(
            username='testuser',
            password='testpass',
            email='test@example.com',
            is_active=True
        )
        self.project = Project.objects.create(
            manager=self.user,
            name='Test Project',
            total_budget=1000
        )
        self.category = ProjectCategory.objects.create(
            project=self.project,
            name='Test Category'
        )

    def test_transaction_serializer_valid_data(self):
        """Test TransactionSerializer with valid input data."""
        data = {
            "user": self.user.id,
            "project": self.project.id,
            "amount": 1000,
            "transaction_category": self.category.id,
            "transaction_note": "Test Note"
        }
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_read_only_fields_are_ignored(self):
        """Test that read-only fields are ignored in serializer."""
        data = {
            "user": self.user.id,
            "project": self.project.id,
            "amount": 1000,
            "transaction_category": self.category.id,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "id": str(uuid4())
        }
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        validated = serializer.validated_data
        self.assertNotIn("created_at", validated)
        self.assertNotIn("updated_at", validated)

    def test_missing_required_fields(self):
        """Test that serializer fails when required fields are missing."""
        data = {}
        serializer = TransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("project", serializer.errors)
        self.assertIn("amount", serializer.errors)
        self.assertIn("transaction_category", serializer.errors)

    def test_optional_transaction_note(self):
        """Test that transaction_note can be blank."""
        data = {
            "user": self.user.id,
            "project": self.project.id,
            "amount": 500,
            "transaction_category": self.category.id
        }
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
