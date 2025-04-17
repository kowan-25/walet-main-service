from django.db import IntegrityError
from django.test import TestCase
from django.core.exceptions import ValidationError
from authentication.models import WaletUser
from projects.models import Project, ProjectCategory
from funds.models import Transaction
from uuid import UUID

class TransactionModelTest(TestCase):
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

    def test_create_valid_transaction(self):
        """Test creating a valid transaction instance."""
        transaction = Transaction.objects.create(
            user=self.user,
            project=self.project,
            amount=1000,
            transaction_category=self.category,
            transaction_note='Test Note'
        )

        self.assertIsInstance(transaction.id, UUID)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.project, self.project)
        self.assertEqual(transaction.amount, 1000)
        self.assertEqual(transaction.transaction_note, 'Test Note')
        self.assertEqual(transaction.transaction_category, self.category)
        self.assertIsNotNone(transaction.created_at)
        self.assertIsNotNone(transaction.updated_at)

    def test_negative_amount_raises_validation_error(self):
        """Test that negative amount raises ValidationError."""
        transaction = Transaction(
            user=self.user,
            project=self.project,
            amount=-100,
            transaction_category=self.category
        )
        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_optional_transaction_note(self):
        """Test that transaction_note can be blank."""
        transaction = Transaction.objects.create(
            user=self.user,
            project=self.project,
            amount=500,
            transaction_category=self.category
        )
        self.assertIsNone(transaction.transaction_note)

    def test_default_created_updated(self):
        """Test that created_at and updated_at are automatically set."""
        transaction = Transaction.objects.create(
            user=self.user,
            project=self.project,
            amount=1000,
            transaction_category=self.category
        )
        self.assertIsNotNone(transaction.created_at)
        self.assertIsNotNone(transaction.updated_at)

    def test_string_representation(self):
        """Test string representation returns user and amount."""
        transaction = Transaction.objects.create(
            user=self.user,
            project=self.project,
            amount=1000,
            transaction_category=self.category
        )
        self.assertEqual(str(transaction), f"{self.user} - 1000")
