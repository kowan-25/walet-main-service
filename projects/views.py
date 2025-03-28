import logging
from uuid import UUID
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction

from authentication.models import WaletUser

from .models import Project, ProjectCategory, ProjectMember
from .serializers import ProjectCategorySerializer, ProjectSerializer

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
            