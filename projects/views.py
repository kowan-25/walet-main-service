from uuid import UUID
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Project, ProjectCategory
from .serializers import ProjectCategorySerializer, ProjectSerializer

# Create your views here.
class GetAllManagedProject(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        projects = Project.objects.filter(manager=request.user.id)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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