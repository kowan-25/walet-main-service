from django.test import TestCase
from django.core.exceptions import ValidationError
from authentication.models import WaletUser
from projects.models import Project, ProjectBudgetRecord
from uuid import UUID

class ProjectBudgetRecordModelTest(TestCase):
    def setUp(self):
        self.user = WaletUser.objects.create_user(
            username='budgetuser',
            password='testpass',
            email='budget@example.com'
        )
        self.project = Project.objects.create(
            manager=self.user,
            name='Budget Project',
            total_budget=10000
        )

    def test_create_income_budget_record(self):
        """Test creating a valid income budget record (member can be None)."""
        record = ProjectBudgetRecord.objects.create(
            project=self.project,
            amount=5000,
            notes='Pemasukan awal',
            is_income=True,
            is_editable=True
        )
        self.assertIsInstance(record.id, UUID)
        self.assertEqual(record.project, self.project)
        self.assertEqual(record.amount, 5000)
        self.assertTrue(record.is_income)
        self.assertIsNone(record.member)
        self.assertIsNotNone(record.created_at)
        self.assertTrue(record.is_editable)

    def test_create_expense_budget_record_with_member(self):
        """Test creating a valid expense budget record (member required)."""
        record = ProjectBudgetRecord.objects.create(
            project=self.project,
            member=self.user,
            amount=2000,
            notes='Pengeluaran untuk user',
            is_income=False,
            is_editable=False
        )
        self.assertEqual(record.member, self.user)
        self.assertFalse(record.is_income)

    def test_create_expense_budget_record_without_member_should_fail(self):
        """Test that expense record without member raises ValidationError."""
        record = ProjectBudgetRecord(
            project=self.project,
            amount=2000,
            notes='Pengeluaran tanpa member',
            is_income=False,
            is_editable=True
        )
        with self.assertRaises(ValidationError):
            record.full_clean()
            record.save()

    def test_amount_cannot_be_negative(self):
        """Test that negative amount raises ValidationError."""
        record = ProjectBudgetRecord(
            project=self.project,
            member=self.user,
            amount=-1000,
            notes='Pengeluaran negatif',
            is_income=False
        )
        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_notes_max_length(self):
        """Test that notes cannot exceed 50 characters."""
        record = ProjectBudgetRecord(
            project=self.project,
            member=self.user,
            amount=1000,
            notes='a' * 51,  # 51 chars
            is_income=False
        )
        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_str_representation(self):
        """Test string representation of ProjectBudgetRecord."""
        record = ProjectBudgetRecord.objects.create(
            project=self.project,
            amount=1000,
            is_income=True
        )
        self.assertIn('Budget Record for', str(record))
