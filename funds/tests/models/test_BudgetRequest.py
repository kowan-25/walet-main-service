import uuid
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.utils import IntegrityError
from django.core.validators import MinValueValidator

from authentication.models import WaletUser
from funds.models import BudgetRequest
from projects.models import Project

class BudgetRequestTests(TestCase):
    def setUp(self):
        """Set up test data for BudgetRequest tests."""
        # Create WaletUser instances
        self.user = WaletUser.objects.create(
            username="testuser",
            email="testuser@example.com",
            password="testpass123"
        )
        self.admin = WaletUser.objects.create(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )

        # Create Project instance
        self.project = Project.objects.create(
            name="Test Project",
            description="A test project",
            manager_id=self.admin.id  # Use the WaletUser instance directly
        )

        # Create BudgetRequest instance
        self.budget_request = BudgetRequest.objects.create(
            project=self.project,
            requested_by=self.user,
            request_reason="Need funds for equipment",
            amount=Decimal("1000.50"),
            status="pending"
        )

    # Model Functionality Tests
    def test_budget_request_creation(self):
        """Test that a BudgetRequest is created correctly."""
        self.assertEqual(self.budget_request.project, self.project)
        self.assertEqual(self.budget_request.requested_by, self.user)
        self.assertEqual(self.budget_request.amount, Decimal("1000.50"))
        self.assertEqual(self.budget_request.status, "pending")
        self.assertTrue(self.budget_request.created_at)
        self.assertIsInstance(self.budget_request.id, uuid.UUID)

    def test_budget_request_str(self):
        """Test the string representation of BudgetRequest."""
        expected_str = f"Budget Request for {self.project} by {self.user} - pending"
        self.assertEqual(str(self.budget_request), expected_str)

    def test_status_choices(self):
        """Test that status choices are respected."""
        self.budget_request.status = "approved"
        self.budget_request.save()
        self.assertEqual(self.budget_request.status, "approved")
        with self.assertRaises(ValidationError):
            self.budget_request.status = "invalid"
            self.budget_request.full_clean()

    def test_amount_validation(self):
        """Test that amount cannot be negative."""
        budget_request = BudgetRequest(
            project=self.project,
            requested_by=self.user,
            request_reason="Invalid amount",
            amount=Decimal("-100.00")
        )
        with self.assertRaises(ValidationError):
            budget_request.full_clean()

    def test_foreign_key_cascade(self):
        """Test that deleting a project deletes associated budget requests."""
        project_id = self.project.id
        self.project.delete()
        self.assertFalse(BudgetRequest.objects.filter(project_id=project_id).exists())

    def test_resolved_by_nullable(self):
        """Test that resolved_by can be null."""
        self.budget_request.resolved_by = None
        self.budget_request.save()
        self.assertIsNone(self.budget_request.resolved_by)

    def test_resolve_note_nullable(self):
        """Test that resolve_note can be null or blank."""
        self.budget_request.resolve_note = ""
        self.budget_request.save()
        self.assertEqual(self.budget_request.resolve_note, "")
        self.budget_request.resolve_note = None
        self.budget_request.save()
        self.assertIsNone(self.budget_request.resolve_note)

    def test_auto_timestamps(self):
        """Test that created_at and resolved_at timestamps are set correctly."""
        self.assertIsNotNone(self.budget_request.created_at)
        self.budget_request.status = "approved"
        self.budget_request.resolved_by = self.admin
        self.budget_request.save()
        self.assertIsNotNone(self.budget_request.resolved_at)

    def test_max_digits_amount(self):
        """Test that amount respects max_digits and decimal_places."""
        budget_request = BudgetRequest(
            project=self.project,
            requested_by=self.user,
            request_reason="Large amount",
            amount=Decimal("9999999999999.99")  # 13 digits + 2 decimal places = 15
        )
        budget_request.full_clean()  # Should pass
        budget_request.amount = Decimal("99999999999999.99")  # Exceeds max_digits
        with self.assertRaises(ValidationError):
            budget_request.full_clean()

    # OWASP-Related Security Tests
    def test_sql_injection_prevention(self):
        """Test that the model prevents SQL injection in text fields."""
        malicious_input = "'); DROP TABLE funds_budgetrequest; --"
        budget_request = BudgetRequest(
            project=self.project,
            requested_by=self.user,
            request_reason=malicious_input,
            amount=Decimal("500.00")
        )
        budget_request.save()
        self.assertEqual(budget_request.request_reason, malicious_input)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM funds_budgetrequest")
            self.assertTrue(cursor.fetchone()[0] > 0)  # Table still exists

    def test_input_validation_text_field(self):
        """Test that text fields handle large or malicious inputs."""
        large_input = "x" * 10000  # Large input to test buffer overflow or truncation
        budget_request = BudgetRequest(
            project=self.project,
            requested_by=self.user,
            request_reason=large_input,
            amount=Decimal("200.00")
        )
        budget_request.save()
        self.assertEqual(budget_request.request_reason, large_input)

        xss_input = "<script>alert('test');</script>"
        budget_request.request_reason = xss_input
        budget_request.save()
        self.assertEqual(budget_request.request_reason, xss_input)
        # Note: Frontend should sanitize this output to prevent XSS

    def test_sensitive_data_exposure(self):
        """Test that sensitive fields are not exposed unnecessarily."""
        budget_request = BudgetRequest.objects.get(id=self.budget_request.id)
        self.assertNotIn(self.user.password, str(budget_request))
        self.assertEqual(budget_request.amount, Decimal("1000.50"))


    def test_required_fields(self):
        """Test that required fields cannot be omitted."""
        budget_request = BudgetRequest(
            project=self.project,
            requested_by=self.user,
            amount=Decimal("100.00")
            # Missing request_reason
        )
        with self.assertRaises(ValidationError):
            budget_request.full_clean()