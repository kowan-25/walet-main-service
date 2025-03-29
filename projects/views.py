import logging
import os
import requests
from uuid import UUID
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction

from authentication.models import WaletUser

from .services import create_budget_records
from .models import Project, ProjectBudgetRecord, ProjectCategory, ProjectInvitation, ProjectMember
from .serializers import ProjectBudgetRecordSerializer, ProjectCategorySerializer, ProjectInvitationSerializer, ProjectMemberSerializer, ProjectSerializer

logger = logging.getLogger(__name__)

# Create your views here.
class GetAllManagedProject(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        projects = Project.objects.filter(manager=request.user.id)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetAllJoinedProject(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        projects_joined = ProjectMember.objects.filter(member=request.user.id)
        projects = [member.project for member in projects_joined]
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetProjectById(APIView):
   
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        is_team_member = ProjectMember.objects.filter(project=project.id, member=request.user.id).exists()
        if project.manager.id == request.user.id or is_team_member:
            serializer = ProjectSerializer(project)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        raise PermissionDenied("You don't have permissions to view this project")

class CreateProject(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ''' Expecting { name, description } key inside request body'''
        with transaction.atomic():
            data = {
                "name": request.data.get("name"),
                "description": request.data.get("description", "")
            }

            serializer = ProjectSerializer(data=data)
            if serializer.is_valid():
                serializer.save(manager=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateProject(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        ''' Expecting { name, description } key inside request body'''
        with transaction.atomic():
            project = get_object_or_404(Project, pk=pk)
            
            data = {
                "name": request.data.get("name"),
                "description": request.data.get("description", "")
            }

            serializer = ProjectSerializer(project, data=data)

            if project.manager.id != request.user.id:
                raise PermissionDenied("You don't have permissions to update this project")

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class DeleteProject(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        with transaction.atomic():
            project = get_object_or_404(Project, pk=pk)

            if project.manager.id != request.user.id:
                raise PermissionDenied("You don't have permissions to delete this project")
            
            project.delete()
            return Response({"message": "Project deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class GetProjectCategories(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        project_categories = ProjectCategory.objects.filter(project=project_id)
        serializer = ProjectCategorySerializer(project_categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetProjectCategoryById(APIView):
   
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        project_category = get_object_or_404(ProjectCategory, pk=pk)
        serializer = ProjectCategorySerializer(project_category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CreateProjectCategory(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ''' Expecting { project_id, name } inside request_body'''
        with transaction.atomic():
            project_id = UUID(request.data.get("project_id"))
            
            data = {
                "name": request.data.get("name"),
                "project": project_id
            }
            serializer = ProjectCategorySerializer(data=data)
            
            # Project Validation
            project = get_object_or_404(Project, pk=project_id)
            if project.manager.id != request.user.id:
                raise PermissionDenied("You don't have permissions to add category to this Project")
            
            if serializer.is_valid():
                serializer.save() 
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteProjectCategory(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        with transaction.atomic():
            category = get_object_or_404(ProjectCategory, pk=pk)

             # Project Validation
            project = category.project
            if project.manager.id != request.user.id:
                raise PermissionDenied("You don't have permissions to delete category to this Project")
            
            ProjectCategory.delete()
            return Response({"message": "category deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        
class RemoveTeamMember(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, project_pk, member_pk):
        with transaction.atomic():
            logger.info(
                f"Delete member: project={project_pk}, member={member_pk}, by user={request.user.id}"
            )
            project = get_object_or_404(Project, pk=project_pk)
            member = get_object_or_404(WaletUser, pk=member_pk)

            project_member = get_object_or_404(ProjectMember, project_id=project.id, member_id=member.id)
            if project.manager.id != request.user.id:
                logger.warning(
                    f"Unauthorized attempt to remove member: user={request.user.id}, project={project_pk}, member={member_pk}"
                )
                raise PermissionDenied("You don't have permissions to remove team members from this project")

            
            project.total_budget = (project.total_budget or 0) + project_member.budget
            project.save()

            project_member.delete()
            logger.info(
                f"Member removed successfully: project={project_pk}, member={member_pk}, by user={request.user.id}"
            )
            return Response({"message": "Member succesfully removed from project"}, status=status.HTTP_204_NO_CONTENT)

class InviteTeamMember(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ''' Expecting { project_id, email } inside request_body'''
        email = request.data.get("email")
        project_id = UUID(request.data.get("project_id"))
        
        if not email or not project_id:
            return Response({"error": "Email and project_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(WaletUser, email=email)
        project = get_object_or_404(Project, id=project_id)

        if project.manager.id != request.user.id:
            raise PermissionDenied("You don't have permissions to invite member to this project")
        
        if ProjectMember.objects.filter(member=user, project=project).exists():
            return Response({"error": "User Already in Project"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # req body
            data = {
                "project": project.id,
                "user": user.id
            }

            serializer = ProjectInvitationSerializer(data=data)
            if serializer.is_valid():
                invitation = serializer.save()
                invite_token = str(invitation.id)
                invite_url = f'http://localhost:8000/api/project/add-member/{invite_token}'  #TODO: change to FE deployment url that include login
                email_payload = {
                    "to": email,
                    "context": {
                        "name": user.username,
                        "project_name": project.name,
                        "invite_link": invite_url
                    }
                }

                try:
                    response = requests.post(f"{os.getenv('NOTIFICATION_URL', 'http://localhost:8001')}/email/invite", json=email_payload)
                    response.raise_for_status()
                except requests.RequestException:
                    return Response({"error": "Failed to send email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({"message": "Invitation sent", "token": invite_token}, status=status.HTTP_200_OK)

class AddTeamMember(APIView):

    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, token):
        invitation = get_object_or_404(ProjectInvitation, pk=token)

        if invitation.user.id != request.user.id:
            return Response({"error": "this invitation is not for you"}, status=status.HTTP_403_FORBIDDEN)
        if invitation.expires_at < timezone.now():
            return Response({"error": "Invitation Expired"}, status=status.HTTP_400_BAD_REQUEST)
        if invitation.is_used:
            return Response({"error": "Invitation Already Used"}, status=status.HTTP_400_BAD_REQUEST)
        if ProjectMember.objects.filter(member=invitation.user, project=invitation.project).exists():
            return Response({"error": "User Already in Project"}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # req body
            data = {
              "member": invitation.user.id,
              "project": invitation.project.id
            }

            serializer = ProjectMemberSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
        
                invitation.is_used = True
                invitation.save(update_fields=["is_used"]) 

                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetProjectBudgets(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        if project.manager.id != request.user.id:
            raise PermissionDenied("You don't have permissions to see budget record from this project")
        
        budget_records = ProjectBudgetRecord.objects.filter(project=project_id)
        serializer = ProjectBudgetRecordSerializer(budget_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetProjectBudgetById(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        budget_records = get_object_or_404(ProjectBudgetRecord, pk=pk)

        if budget_records.project.manager.id != request.user.id:
            raise PermissionDenied("You don't have permissions to see this budget record")
        
        serializer = ProjectBudgetRecordSerializer(budget_records)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AddProjectBudget(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ''' Expecting { project_id, amount, notes } inside request_body'''
        project_id = UUID(request.data["project_id"])
        amount = request.data.get("amount")
        notes = request.data.get("notes", "-") #optional

        data, status = create_budget_records(project_id, amount, notes, request.user.id, is_editable=True)
        return Response(data, status=status)

class UpdateProjectBudget(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        ''' Expecting { amount, notes } inside request_body'''
        budget_records = get_object_or_404(ProjectBudgetRecord, pk=pk)
        amount = request.data.get("amount", budget_records.amount)
        notes = request.data.get("notes", budget_records.notes)
        
        if budget_records.project.manager.id != request.user.id:
            raise PermissionDenied("You don't have permissions to update this budget record")
        
        if budget_records.is_editable:
            with transaction.atomic():
                budget_records.amount = amount
                budget_records.notes = notes
                budget_records.save()
                return Response({"detail": f"succesfully updated budget record {budget_records.id}"}, status=status.HTTP_200_OK)
        
        return Response({"error": "this budget record is uneditable"}, status=status.HTTP_403_FORBIDDEN)

class DeleteProjectBudget(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        budget_records = get_object_or_404(ProjectBudgetRecord, pk=pk)
        
        if budget_records.project.manager.id != request.user.id:
            raise PermissionDenied("You don't have permissions to delete this budget record")
        
        if budget_records.is_editable:
            with transaction.atomic():
                budget_records.delete()
                return Response({"detail": f"succesfully deleted budget record {budget_records.id}"}, status=status.HTTP_200_OK)
        
        return Response({"error": "this budget record is uneditable"}, status=status.HTTP_403_FORBIDDEN)