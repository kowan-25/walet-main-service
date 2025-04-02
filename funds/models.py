import uuid
from django.db import models
from authentication.models import WaletUser
from projects.models import Project, ProjectCategory
from django.core.validators import MinValueValidator
    
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(WaletUser, on_delete=models.CASCADE, db_column='user_id')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, db_column='project_id')
    amount = models.IntegerField(validators=[MinValueValidator(0)])
    transaction_note = models.TextField(blank=True, null=True)
    transaction_category = models.ForeignKey(ProjectCategory, on_delete=models.CASCADE, db_column='transaction_category')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.amount}"

class BudgetRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, db_column='project_id')
    requested_by = models.ForeignKey(
        WaletUser, 
        on_delete=models.CASCADE, 
        related_name='budget_requests_made', 
        db_column='requested_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    request_reason = models.TextField()
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(0)], 
        default=0
    )
    resolve_note = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(auto_now_add=True)
    resolved_by = models.ForeignKey(
        WaletUser,
        on_delete=models.SET_NULL, 
        related_name='budget_requests_resolved', 
        blank=True,
        null=True,
        db_column='resolved_by'
    )

    def __str__(self):
        return f"Budget Request for {self.project} by {self.requested_by} - {self.status}"