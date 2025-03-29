from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework import status

from .serializers import ProjectBudgetRecordSerializer
from .models import Project


def create_budget_records(project_id, amount, notes, manager_id, is_income=True, member_id=None, is_editable=False):
    project = get_object_or_404(Project, pk=project_id)
       
    if project.manager.id != manager_id:
        raise PermissionDenied("You don't have permissions to add budget record to this project")
    
    # expected req body
    data = {
        "project": project_id,
        "member": member_id,
        "amount": amount,
        "notes": notes,
        "is_income": is_income,
        "is_editable": is_editable
    }

    serializer = ProjectBudgetRecordSerializer(data=data)
    if serializer.is_valid():
        try:
            budget_record = serializer.save()
            
            if budget_record.is_income:
                project.total_budget += int(amount)
            else:
                project.total_budget -= int(amount)
            
            project.save()
       
        except ValidationError as e:
            return {'error': str(e)}, status.HTTP_400_BAD_REQUEST

        return serializer.data, status.HTTP_200_OK
    return serializer.errors, status.HTTP_400_BAD_REQUEST