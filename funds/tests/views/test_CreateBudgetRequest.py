import uuid
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
from authentication.models import WaletUser
from projects.models import Project, ProjectMember
from funds.models import BudgetRequest
from funds.serializers import BudgetRequestSerializer

class CreateBudgetRequestTests(TestCase):
    def setUp(self):
        """Set up test data for CreateBudgetRequest tests."""
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

        self.project = Project.objects.create(
            name="Test Project",
            description="A test project",
            manager_id=self.manager.id,
            total_budget=5000
        )

        self.project_member = ProjectMember.objects.create(
            member=self.user,
            project=self.project,
            budget=1000
        )

        self.client = APIClient()
        self.url = reverse('create-budget-request')  

    def test_create_budget_request_success(self):
        """Test successful creation of a budget request."""
        self.client.force_authenticate(user=self.user)
        data = {
            "project_id": str(self.project.id),
            "request_reason": "Need funds for equipment",
            "amount": "2000"
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "sent"}

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["request_reason"], "Need funds for equipment")
            self.assertEqual(response.data["amount"], "2000.00")

            budget_request = BudgetRequest.objects.get(id=response.data["id"])
            self.assertEqual(budget_request.project, self.project)
            self.assertEqual(budget_request.requested_by, self.user)
            self.assertEqual(budget_request.amount, Decimal("2000"))

            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            self.assertEqual(call_args["json"]["to"], self.manager.email)
            self.assertEqual(call_args["json"]["context"]["project_name"], self.project.name)

    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected."""
        data = {
            "project_id": str(self.project.id),
            "request_reason": "Need funds",
            "amount": "1000"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Authentication credentials were not provided.")

    def test_invalid_project_id(self):
        """Test that a non-existent project_id is rejected."""
        self.client.force_authenticate(user=self.user)
        data = {
            "project_id": str(uuid.uuid4()), 
            "request_reason": "Need funds",
            "amount": "1000"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_not_project_member(self):
        """Test that a user who is not a project member is rejected."""
        non_member = WaletUser.objects.create_user(
            username="nonmember",
            email="nonmember@example.com",
            password="nonmemberpass123"
        )
        self.client.force_authenticate(user=non_member)
        data = {
            "project_id": str(self.project.id),
            "request_reason": "Need funds",
            "amount": "1000"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_notification_failure(self):
        """Test that a notification failure returns an error."""
        self.client.force_authenticate(user=self.user)
        data = {
            "project_id": str(self.project.id),
            "request_reason": "Need funds",
            "amount": "1000"
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 500
            mock_post.return_value.json.return_value = {"error": "Notification service down"}

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.data["error"], "Failed to send notification")
            self.assertEqual(response.data["details"], {"error": "Notification service down"})

            self.assertFalse(BudgetRequest.objects.filter(project=self.project).exists())

    def test_sql_injection_in_request_reason(self):
        """Test that malicious SQL inputs in request_reason are safely handled."""
        self.client.force_authenticate(user=self.user)
        malicious_input = "'); DROP TABLE funds_budgetrequest; --"
        data = {
            "project_id": str(self.project.id),
            "request_reason": malicious_input,
            "amount": "1000"
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "sent"}

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["request_reason"], malicious_input)

            budget_request = BudgetRequest.objects.get(id=response.data["id"])
            self.assertEqual(budget_request.request_reason, malicious_input)

    def test_xss_in_request_reason(self):
        """Test that XSS inputs in request_reason are safely stored."""
        self.client.force_authenticate(user=self.user)
        xss_input = "<script>alert('test');</script>"
        data = {
            "project_id": str(self.project.id),
            "request_reason": xss_input,
            "amount": "1000"
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "sent"}

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["request_reason"], xss_input)