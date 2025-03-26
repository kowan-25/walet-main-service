from django.db import models
from django.core.validators import MinValueValidator
from authentication.models import WaletUser

import uuid

# Create your models here.
class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manager = models.ForeignKey(WaletUser, on_delete=models.CASCADE, db_column='manager_id')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    total_budget = models.IntegerField(validators=[MinValueValidator(0, message="Total budget can not be negative")], default=0)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class ProjectCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, db_column='project_id')
    name = models.CharField(max_length=255)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project_id', 'name'], name='unique_project_category')
        ]

    def __str__(self):
        return self.name + " " + self.project.name