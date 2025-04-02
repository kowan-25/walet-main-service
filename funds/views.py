from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Transaction
from .serializers import TransactionSerializer
from projects.models import Project

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