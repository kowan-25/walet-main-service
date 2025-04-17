from django.test import TestCase
from authentication.models import WaletUser
from projects.models import Project, ProjectBudgetRecord
from projects.serializers import ProjectBudgetRecordSerializer

class ProjectBudgetRecordSerializerTest(TestCase):
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

    def test_serializer_valid_income(self):
        """Test serializer with valid income data (no member)."""
        data = {
            "project": self.project.id,
            "amount": 5000,
            "is_income": True,
            "is_editable": True,
            "notes": "Pemasukan awal"
        }
        serializer = ProjectBudgetRecordSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_valid_expense(self):
        """Test serializer with valid expense data (member required)."""
        data = {
            "project": self.project.id,
            "member": self.user.id,
            "amount": 2000,
            "is_income": False,
            "is_editable": False,
            "notes": "Pengeluaran"
        }
        serializer = ProjectBudgetRecordSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_expense_without_member_invalid(self):
        """Test serializer invalid if expense and member is None."""
        data = {
            "project": self.project.id,
            "amount": 2000,
            "is_income": False,
            "is_editable": True,
            "notes": "Pengeluaran tanpa member"
        }
        serializer = ProjectBudgetRecordSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # serializer is valid, but model validation will fail on save

        # Simulate save to trigger model validation
        with self.assertRaises(Exception):
            serializer.save()

    def test_serializer_negative_amount(self):
        """Test serializer invalid if amount is negative."""
        data = {
            "project": self.project.id,
            "member": self.user.id,
            "amount": -500,
            "is_income": False,
            "is_editable": True,
            "notes": "Negatif"
        }
        serializer = ProjectBudgetRecordSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_serializer_notes_too_long(self):
        """Test serializer invalid if notes > 50 chars."""
        data = {
            "project": self.project.id,
            "member": self.user.id,
            "amount": 1000,
            "is_income": False,
            "is_editable": True,
            "notes": "a" * 51
        }
        serializer = ProjectBudgetRecordSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("notes", serializer.errors)
