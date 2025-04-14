import os
from uuid import UUID

import requests
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from .models import BudgetRequest, Transaction
from .services import send_funds, take_funds
from .serializers import BudgetRequestSerializer, TransactionSerializer
from projects.models import Project, ProjectMember

class GetProjectTransaction(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        if project.manager.id != request.user.id:
            raise PermissionDenied("You don't have permissions to view this project transaction")

        tx = Transaction.objects.filter(project=project_id)
        serializer = TransactionSerializer(tx, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetMemberTransaction(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id, user_id):
        if user_id != request.user.id:
            raise PermissionDenied("You don't have permissions to view this member transaction")

        tx = Transaction.objects.filter(project=project_id, user=user_id)
        serializer = TransactionSerializer(tx, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetTransactionById(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk)
        # Verify user has access to this transaction's project
        if transaction.user.id != request.user.id:
            raise PermissionDenied("You don't have permissions to view this transaction")
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CreateTransaction(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ''' Expecting { project_id, amount, transaction_note, transaction_category } key inside request_body'''
        data = {
            "project": UUID(request.data.get("project_id")),
            "amount": request.data.get("amount"),
            "transaction_note": request.data.get("transaction_note", ""),
            "transaction_category": UUID(request.data.get("category_id"))
        }

        member = get_object_or_404(ProjectMember, project=data["project"], member=request.user)
        if member.budget < data["amount"]:
            return Response({"error": "not enough amount"}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            serializer = TransactionSerializer(data=data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                member.budget -= int(data["amount"])
                member.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateTransaction(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        ''' Expecting { amount, transaction_note, transaction_category } key inside request_body'''
        tx = get_object_or_404(Transaction, pk=pk)
        if tx.user.id != request.user.id:
            raise PermissionDenied("You don't have permissions to edit this transaction")
        
        data = {
            "project": tx.project.id,
            "amount": request.data.get("amount", tx.amount),
            "transaction_note": request.data.get("transaction_note", tx.transaction_note),
            "transaction_category": request.data.get("category_id", tx.transaction_category.id)
        }

        member = get_object_or_404(ProjectMember, project=data["project"], member=request.user.id)
        if (member.budget + tx.amount) < int(request.data.get("amount")):
            return Response({"error": "not enough amount"}, status=status.HTTP_400_BAD_REQUEST)
        

        with transaction.atomic():
            serializer = TransactionSerializer(tx, data=data)
            if serializer.is_valid():
                #add back previous transaction budget then substract it with new transaction budget
                member.budget = member.budget - int(data["amount"]) + tx.amount
                member.save()

                serializer.save()
                
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteTransaction(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        with transaction.atomic():
            tx = get_object_or_404(Transaction, pk=pk)
            
            if tx.user.id != request.user.id:
                raise PermissionDenied("You don't have permissions to delete this transaction")
            
            # add back deleted transaction amount to the member budget
            member = get_object_or_404(ProjectMember, project=tx.project, member=tx.user)
            member.budget += tx.amount
            member.save()

            tx.delete()
            return Response({"message": "Transaction deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        

class SendFunds(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, project_id):
        ''' Expecting { member_id, funds, notes } key inside request_body'''
        project = get_object_or_404(Project, pk=project_id)
        if project.manager.id != request.user.id:
            raise PermissionDenied("You don't have permissions to send funds")
        
        member_id = UUID(request.data.get("member_id"))
        funds = request.data.get("funds")
        notes = request.data.get("notes", "-")
        data, status = send_funds(project_id, member_id, funds, notes, request.user.id)
        return Response(data, status=status)

class TakeFunds(APIView):

     permission_classes = [permissions.IsAuthenticated]

     def post(self, request, project_id):
          ''' Expecting { member_id, funds, notes } key inside request_body'''
          member_id = UUID(request.data.get("member_id"))
          funds = request.data.get("funds")
          notes = request.data.get("notes", "-")
          data, status = take_funds(project_id, member_id, funds, notes, request.user.id)
          return Response(data, status=status)
     
class GetUserBudgetRequests(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        budget_requests = BudgetRequest.objects.filter(requested_by=request.user.id)
        
        status_filter = request.query_params.get('status')
        if status_filter in ['pending', 'approved', 'rejected']:
            budget_requests = budget_requests.filter(status=status_filter)
        
        serializer = BudgetRequestSerializer(budget_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class GetUserBudgetRequestsByProjectId(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        budget_requests = BudgetRequest.objects.filter(requested_by=request.user.id)
        budget_requests = budget_requests.filter(project=project_id)
        
        status_filter = request.query_params.get('status')
        if status_filter in ['pending', 'approved', 'rejected']:
            budget_requests = budget_requests.filter(status=status_filter)
        
        serializer = BudgetRequestSerializer(budget_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class GetBudgetRequestsByProjectId(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        budget_requests = BudgetRequest.objects.select_related('requested_by').filter(project=project_id)
        
        status_filter = request.query_params.get('status')
        if status_filter in ['pending', 'approved', 'rejected']:
            budget_requests = budget_requests.filter(status=status_filter)
        
        serializer = BudgetRequestSerializer(budget_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetBudgetRequestById(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        budget_request = get_object_or_404(BudgetRequest, id=pk)
        
        if budget_request.requested_by != request.user:
            raise PermissionDenied("You don't have permissions to view this budget request")

        serializer = BudgetRequestSerializer(budget_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CreateBudgetRequest(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ''' Expecting { project_id, amount, request_reason } key inside request_body'''
        with transaction.atomic():
            project_id = UUID(request.data.get("project_id"))
            request_reason = request.data.get("request_reason")
            amount = request.data.get("amount")

            if not project_id or not request_reason:
                return Response(
                    {"error": "project_id and request_reason are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            project = get_object_or_404(Project, pk=project_id)
            member = get_object_or_404(ProjectMember, project=project_id, member=request.user.id)

            if project.total_budget < int(amount):
                return Response( 
                    {"error": "the amount of your request is higher than project total budget"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = {
                "project": project_id,
                "request_reason": request_reason,
                "amount": amount
            }

            serializer = BudgetRequestSerializer(data=data)
            if serializer.is_valid():
                notification_url = os.getenv("NOTIFICATION_URL", "http://localhost:8001") + "/email/fund-request"
                notification_data = {
                    "to": project.manager.email,
                    "context": {
                        "recipient_name": project.manager.username,
                        "sender_name": member.member.username,
                        "action_link": f"http://localhost:3000/dashboard/{project_id}/fund-requests",
                        "project_name": project.name,
                        "fund_total": amount
                    }
                }

                response = requests.post(notification_url, json=notification_data, verify=False)
                if response.status_code != 200:
                    return Response(
                        {"error": "Failed to send notification", "details": response.json()},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                serializer.save(requested_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
class ResolveBudgetRequest(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        ''' Expecting { resolve_note, action } key inside request_body'''
        try:
            with transaction.atomic():  
                budget_request = get_object_or_404(BudgetRequest, pk=pk)
                project = budget_request.project
                if project.manager.id != request.user.id:
                    raise PermissionDenied("You don't have permissions to resolve this budget request")


                if budget_request.status != 'pending':
                    return Response({"error": "This request has already been resolved"}, status=status.HTTP_400_BAD_REQUEST)

                action = request.data.get("action") 
                resolve_note = request.data.get("resolve_note", "")

                if action not in ['approve', 'reject']:
                    return Response({"error": "Action must be 'approve' or 'reject'"}, status=status.HTTP_400_BAD_REQUEST)

                budget_request.status = 'approved' if action == 'approve' else 'rejected'
                budget_request.resolve_note = resolve_note
                budget_request.resolved_at = timezone.now()
                budget_request.resolved_by = request.user

                if budget_request.status == 'approved':
                    if budget_request.amount <= 0:
                        return Response(
                            {"error": "Amount must be positive"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    if project.total_budget < budget_request.amount:
                        return Response(
                            {"error": "Insufficient project budget to approve this request"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    data, status_code = send_funds(project.id, budget_request.requested_by.id, int(budget_request.amount), "approved budget request", request.user.id)

                    if status_code != status.HTTP_200_OK:
                        return Response(data, status=status_code)

                budget_request.save()

                # Email Notification
                notification_url = os.getenv("NOTIFICATION_URL", "http://localhost:8001") + "/email/fund-approval"
                email_payload = {
                    "to": budget_request.requested_by.email,
                    "context": {
                        "recipient_name": budget_request.requested_by.username,
                        "project_name": project.name,
                        "status": budget_request.status
                    }
                }

                response = requests.post(notification_url, json=email_payload, verify=False)
                if response.status_code != 200:
                    return Response(
                        {"error": "Failed to send notification", "details": response.json()},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                return Response(
                    {"message": f"Budget request {budget_request.status}"},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    