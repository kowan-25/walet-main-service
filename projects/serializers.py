from rest_framework import serializers
from .models import Project, ProjectCategory

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'manager', 'total_budget')

class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCategory
        fields = '__all__'
        read_only_fields = ('id',)