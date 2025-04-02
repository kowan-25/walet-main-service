from uuid import UUID
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Transaction
from .serializers import TransactionSerializer
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