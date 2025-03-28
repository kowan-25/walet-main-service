from django.db import models
from django.core.validators import MinValueValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import uuid

from authentication.models import WaletUser

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
    
class ProjectMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(WaletUser, on_delete=models.CASCADE, db_column='member_id')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, db_column='project_id')
    budget = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project_id', 'member_id'], name='unique_member_project')
        ]
    
    def __str__(self):
        return f"{self.member.username} in Project {self.project.name}"

def get_expiry():
    return timezone.now() + timedelta(days=3)
class ProjectInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, db_column='project_id')
    user = models.ForeignKey(WaletUser, on_delete=models.CASCADE, db_column='user_id')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=get_expiry)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Invitation for {self.user.username} to join {self.project.name}"

class ProjectBudgetRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, db_column='project_id')
    member = models.ForeignKey(WaletUser, on_delete=models.CASCADE, db_column='user_id', null=True , blank=True)
    amount = models.IntegerField(validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True, null= True, validators=[MaxLengthValidator(50)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_income = models.BooleanField()
    is_editable = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.is_income and self.member is None:
            raise ValidationError("Member cannot be null for expense records.")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Budget Record for {self.project.name} ({'Income' if self.is_income else 'Expense'}): {self.amount}"

