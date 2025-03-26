from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Project
from .serializers import ProjectSerializer

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