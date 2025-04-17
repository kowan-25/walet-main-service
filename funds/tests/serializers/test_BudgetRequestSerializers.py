import uuid
from decimal import Decimal
from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import serializers
from django.utils import timezone
from authentication.models import WaletUser
from funds.models import BudgetRequest
from funds.serializers import BudgetRequestSerializer
from projects.models import Project

class BudgetRequestSerializerTests(TestCase):
    def setUp(self):
        """Set up test data for BudgetRequestSerializer tests."""
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

        self.budget_request = BudgetRequest.objects.create(
            project=self.project,
            requested_by=self.user,
            request_reason="Need funds for equipment",
            amount=Decimal("1000.50"),
            status="pending"
        )

        self.client = APIClient()

    def test_serialize_budget_request(self):
        """Test that BudgetRequestSerializer correctly serializes a BudgetRequest instance."""
        serializer = BudgetRequestSerializer(self.budget_request)
        data = serializer.data

        self.assertEqual(data['id'], str(self.budget_request.id))
        self.assertEqual(data['request_reason'], "Need funds for equipment")
        self.assertEqual(data['amount'], "1000.50")
        self.assertEqual(data['status'], "pending")
        self.assertIsNone(data['resolve_note'])
        self.assertIsNone(data['resolved_by'])
        self.assertTrue(data['created_at'])
        self.assertTrue(data['resolved_at'])

    def test_deserialize_create_budget_request(self):
        """Test that BudgetRequestSerializer can create a new BudgetRequest."""
        data = {
            "project": str(self.project.id),
            "request_reason": "Need funds for software",
            "amount": "2000.00",
            "status": "pending",
            "resolve_note": "Initial note",
            "resolved_by": str(self.admin.id)
        }
        serializer = BudgetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        budget_request = serializer.save(requested_by=self.user) 

        self.assertEqual(budget_request.project, self.project)
        self.assertEqual(budget_request.requested_by, self.user)
        self.assertEqual(budget_request.request_reason, "Need funds for software")
        self.assertEqual(budget_request.amount, Decimal("2000.00"))
        self.assertEqual(budget_request.status, "pending")
        self.assertEqual(budget_request.resolve_note, "Initial note")
        self.assertEqual(budget_request.resolved_by, self.admin)

    def test_read_only_fields(self):
        """Test that read-only fields cannot be modified."""
        data = {
            "project": str(self.project.id),
            "request_reason": "Updated reason",
            "amount": "1500.00",
            "status": "approved",
            "id": str(uuid.uuid4()),  
            "created_at": timezone.now().isoformat(),
            "resolved_at": timezone.now().isoformat(),
            "requested_by": str(self.admin.id)
        }
        serializer = BudgetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        budget_request = serializer.save(requested_by=self.user)

        # Verify read-only fields are not overridden
        self.assertNotEqual(budget_request.id, data['id'])
        self.assertNotEqual(budget_request.created_at.isoformat(), data['created_at'])
        self.assertNotEqual(budget_request.resolved_at.isoformat(), data['resolved_at'])
        self.assertEqual(budget_request.requested_by, self.user)  # Set by view, not data

    def test_negative_amount_validation(self):
        """Test that negative amounts are rejected."""
        data = {
            "project": str(self.project.id),
            "request_reason": "Invalid amount",
            "amount": "-100.00",
            "status": "pending"
        }
        serializer = BudgetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        self.assertEqual(
            serializer.errors["amount"][0].code,
            "min_value",
            "Expected min_value error for negative amount"
        )

    def test_invalid_status_validation(self):
        """Test that invalid status choices are rejected."""
        data = {
            "project": str(self.project.id),
            "request_reason": "Invalid status",
            "amount": "500.00",
            "status": "invalid"
        }
        serializer = BudgetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)
        self.assertEqual(
            serializer.errors["status"][0].code,
            "invalid_choice",
            "Expected invalid_choice error for invalid status"
        )

    def test_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        data = {
            "project": str(self.project.id),
            "amount": "500.00",
            "status": "pending"
            # Missing request_reason
        }
        serializer = BudgetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("request_reason", serializer.errors)
        self.assertEqual(
            serializer.errors["request_reason"][0].code,
            "required",
            "Expected required error for missing request_reason"
        )

    def test_invalid_project_id(self):
        """Test that an invalid project ID is rejected."""
        data = {
            "project": str(uuid.uuid4()),  # Non-existent project
            "request_reason": "Invalid project",
            "amount": "500.00",
            "status": "pending"
        }
        serializer = BudgetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("project", serializer.errors)
        self.assertEqual(
            serializer.errors["project"][0].code,
            "does_not_exist",
            "Expected does_not_exist error for invalid project ID"
        )

    # OWASP-Related Security Tests
    def test_sql_injection_in_text_fields(self):
        """Test that malicious SQL inputs are safely handled."""
        malicious_input = "'); DROP TABLE funds_budgetrequest; --"
        data = {
            "project": str(self.project.id),
            "request_reason": malicious_input,
            "amount": "500.00",
            "status": "pending",
            "resolve_note": malicious_input
        }
        serializer = BudgetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        budget_request = serializer.save(requested_by=self.user)

        self.assertEqual(budget_request.request_reason, malicious_input)
        self.assertEqual(budget_request.resolve_note, malicious_input)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM funds_budgetrequest")
            self.assertTrue(cursor.fetchone()[0] > 0)

    def test_xss_in_text_fields(self):
        """Test that XSS inputs are safely stored (sanitization should happen in frontend)."""
        xss_input = "<script>alert('test');</script>"
        data = {
            "project": str(self.project.id),
            "request_reason": xss_input,
            "amount": "500.00",
            "status": "pending",
            "resolve_note": xss_input
        }
        serializer = BudgetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        budget_request = serializer.save(requested_by=self.user)

        self.assertEqual(budget_request.request_reason, xss_input)
        self.assertEqual(budget_request.resolve_note, xss_input)

    def test_sensitive_data_exposure(self):
        """Test that sensitive data (e.g., password) is not exposed in serialized output."""
        serializer = BudgetRequestSerializer(self.budget_request)
        data = serializer.data

        self.assertNotIn("password", data)
        self.assertEqual(data["amount"], "1000.50")

    def test_large_input_validation(self):
        """Test that large inputs in text fields are handled correctly."""
        large_input = "x" * 10000
        data = {
            "project": str(self.project.id),
            "request_reason": large_input,
            "amount": "500.00",
            "status": "pending",
            "resolve_note": large_input
        }
        serializer = BudgetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        budget_request = serializer.save(requested_by=self.user)

        self.assertEqual(budget_request.request_reason, large_input)
        self.assertEqual(budget_request.resolve_note, large_input)