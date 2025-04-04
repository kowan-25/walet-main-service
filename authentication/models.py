import re
from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.core.exceptions import ValidationError

class WaletUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class WaletUser(AbstractBaseUser):
    # Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)      # Must be True for admin access
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    # Required fields for AbstractBaseUser
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    # Custom manager
    objects = WaletUserManager()

    def __str__(self):
        return self.username
    
    # REQUIRED METHODS FOR ADMIN PERMISSIONS (if not using PermissionsMixin)
    def has_perm(self, perm, obj=None):
        return self.is_superuser  # Superusers have all permissions

    def has_module_perms(self, app_label):
        return self.is_superuser  # Superusers can access all modules
    
    def clean(self):
        super().clean()
        # Password validation
        if self.password:
            if len(self.password) < 8:
                raise ValidationError('Password must be at least 8 characters long.')
            if not re.search(r'\d', self.password):
                raise ValidationError('Password must contain at least one number.')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', self.password):
                raise ValidationError('Password must contain at least one special character.')
