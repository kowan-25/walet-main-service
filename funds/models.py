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