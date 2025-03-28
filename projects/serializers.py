from rest_framework import serializers
from .models import Project, ProjectCategory, ProjectInvitation, ProjectMember

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

class ProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class ProjectInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectInvitation
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'expires_at', 'is_used')