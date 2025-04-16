import uuid
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from unittest.mock import patch
from authentication.models import WaletUser
from projects.models import Project
from funds.models import BudgetRequest

class ResolveBudgetRequestTests(TestCase):
    def setUp(self):
        """Set up test data for ResolveBudgetRequest tests."""
        self.user = WaletUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123"
        )
        self.manager = WaletUser.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="managerpass123"
        )
        self.non_manager = WaletUser.objects.create_user(
            username="nonmanager",
            email="nonmanager@example.com",
            password="nonmanagerpass123"
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="A test project",
            manager_id=self.manager.id,
            total_budget=5000
        )

        self.budget_request = BudgetRequest.objects.create(
            project=self.project,
            requested_by=self.user,
            request_reason="Need funds for equipment",
            amount=Decimal("2000.50"),
            status="pending"
        )

        self.client = APIClient()
        self.url = reverse('resolve-budget-request', kwargs={'pk': str(self.budget_request.id)})

    def test_approve_budget_request_success(self):
        """Test successful approval of a budget request."""
        self.client.force_authenticate(user=self.manager)
        data = {
            "action": "approve",
            "resolve_note": "Approved for equipment purchase"
        }

        with patch('funds.views.send_funds') as mock_send_funds, patch('requests.post') as mock_post:
            mock_send_funds.return_value = ({"status": "success"}, status.HTTP_200_OK)
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "sent"}

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["message"], "Budget request approved")

            budget_request = BudgetRequest.objects.get(id=self.budget_request.id)
            self.assertEqual(budget_request.status, "approved")
            self.assertEqual(budget_request.resolve_note, "Approved for equipment purchase")
            self.assertIsNotNone(budget_request.resolved_at)
            self.assertEqual(budget_request.resolved_by, self.manager)

            mock_send_funds.assert_called_once_with(
                self.project.id,
                self.user.id,
                int(self.budget_request.amount),
                "approved budget request",
                self.manager.id
            )

            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            self.assertEqual(call_args["json"]["to"], self.user.email)
            self.assertEqual(call_args["json"]["context"]["status"], "approved")

    def test_reject_budget_request_success(self):
        """Test successful rejection of a budget request."""
        self.client.force_authenticate(user=self.manager)
        data = {
            "action": "reject",
            "resolve_note": "Insufficient justification"
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "sent"}

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["message"], "Budget request rejected")

            # Verify database state
            budget_request = BudgetRequest.objects.get(id=self.budget_request.id)
            self.assertEqual(budget_request.status, "rejected")
            self.assertEqual(budget_request.resolve_note, "Insufficient justification")
            self.assertIsNotNone(budget_request.resolved_at)
            self.assertEqual(budget_request.resolved_by, self.manager)

            # Verify notification call
            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            self.assertEqual(call_args["json"]["to"], self.user.email)
            self.assertEqual(call_args["json"]["context"]["status"], "rejected")

    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected."""
        data = {
            "action": "approve",
            "resolve_note": "Test note"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Authentication credentials were not provided.")


    def test_non_pending_request(self):
        """Test that non-pending requests cannot be resolved."""
        self.budget_request.status = "approved"
        self.budget_request.save()
        self.client.force_authenticate(user=self.manager)
        data = {
            "action": "reject",
            "resolve_note": "Test note"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "This request has already been resolved")

    def test_invalid_action(self):
        """Test that invalid actions are rejected."""
        self.client.force_authenticate(user=self.manager)
        data = {
            "action": "invalid",
            "resolve_note": "Test note"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Action must be 'approve' or 'reject'")

    def test_zero_amount_approval(self):
        """Test that approving a request with zero amount is rejected."""
        self.budget_request.amount = Decimal("0")
        self.budget_request.save()
        self.client.force_authenticate(user=self.manager)
        data = {
            "action": "approve",
            "resolve_note": "Test note"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Amount must be positive")

    def test_insufficient_budget_approval(self):
        """Test that approving a request exceeding total_budget is rejected."""
        self.budget_request.amount = Decimal("6000") 
        self.budget_request.save()
        self.client.force_authenticate(user=self.manager)
        data = {
            "action": "approve",
            "resolve_note": "Test note"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Insufficient project budget to approve this request"
        )

    def test_send_funds_failure(self):
        """Test that a send_funds failure returns an error."""
        self.client.force_authenticate(user=self.manager)
        data = {
            "action": "approve",
            "resolve_note": "Test note"
        }

        with patch('funds.views.send_funds') as mock_send_funds:
            mock_send_funds.return_value = (
                {"error": "Insufficient funds"},
                status.HTTP_400_BAD_REQUEST
            )

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data["error"], "Insufficient funds")

            budget_request = BudgetRequest.objects.get(id=self.budget_request.id)
            self.assertEqual(budget_request.status, "pending")

    def test_invalid_budget_request_id(self):
        """Test that a non-existent budget request ID is rejected."""
        self.client.force_authenticate(user=self.manager)
        invalid_url = reverse('resolve-budget-request', kwargs={'pk': str(uuid.uuid4())})
        data = {
            "action": "approve",
            "resolve_note": "Test note"
        }
        response = self.client.post(invalid_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_sql_injection_in_resolve_note(self):
        """Test that malicious SQL inputs in resolve_note are safely handled."""
        self.client.force_authenticate(user=self.manager)
        malicious_input = "'); DROP TABLE funds_budgetrequest; --"
        data = {
            "action": "reject",
            "resolve_note": malicious_input
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "sent"}

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["message"], "Budget request rejected")

            budget_request = BudgetRequest.objects.get(id=self.budget_request.id)
            self.assertEqual(budget_request.resolve_note, malicious_input)

    def test_xss_in_resolve_note(self):
        """Test that XSS inputs in resolve_note are safely stored."""
        self.client.force_authenticate(user=self.manager)
        xss_input = "<script>alert('test');</script>"
        data = {
            "action": "reject",
            "resolve_note": xss_input
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "sent"}

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["message"], "Budget request rejected")

            budget_request = BudgetRequest.objects.get(id=self.budget_request.id)
            self.assertEqual(budget_request.resolve_note, xss_input)