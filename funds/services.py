from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from django.db import transaction

from projects.models import Project, ProjectMember
from projects.services import create_budget_records


def send_funds(project_id, member_id, funds, notes, manager_id):
    try:
        funds = int(funds)
        if funds <= 0:
            return {"error": "Funds must be positive"}, status.HTTP_400_BAD_REQUEST

        project = get_object_or_404(Project, pk=project_id)
        member = get_object_or_404(ProjectMember, member=member_id, project=project_id)

        if project.manager.id != manager_id:
            raise PermissionDenied("You don't have permissions to send funds in this project")

        if project.total_budget < funds:
            return {"error": "Project budget is not sufficient"}, status.HTTP_400_BAD_REQUEST

        with transaction.atomic():
            member.budget += funds
            member.save()

            create_budget_records(project_id, funds, notes, is_income=False, manager_id=manager_id, member_id=member_id)

        data = {
            "message": "Funds sent successfully",
            "project_remaining_budget": project.total_budget,
            "member_new_budget": member.budget
        }

        return data, status.HTTP_200_OK

    except (KeyError, ValueError):
        return {"error": "Invalid input data"}, status.HTTP_400_BAD_REQUEST