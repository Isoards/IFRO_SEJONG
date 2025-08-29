import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
import uuid
import secrets
import string
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    ROLE_CHOICES = [
        ('operator', 'Operator'),
        ('admin', 'Administrator'),
    ]
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name='Email'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Name'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='operator',
        verbose_name='Role'
    )
    admin_code_used = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Admin Code Used'
    )
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_permissions_set',
        related_query_name='user',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    password_salt = models.CharField(max_length=32, blank=True)
    
    class Meta:
        db_table = 'user_auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_operator(self):
        return self.role == 'operator'
    
    def save(self, *args, **kwargs):
        """Automatically set Django Admin permissions based on role"""
        # Grant staff permissions for admin role
        if self.role == 'admin':
            self.is_staff = True
        super().save(*args, **kwargs)

class AdminCode(models.Model):
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Admin Code'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Description'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    max_uses = models.PositiveIntegerField(
        default=1,
        verbose_name='Max Uses'
    )
    current_uses = models.PositiveIntegerField(
        default=0,
        verbose_name='Current Uses'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Expires At'
    )
    auto_generate = models.BooleanField(
        default=False,
        verbose_name='Auto Generate'
    )
    generation_interval_hours = models.PositiveIntegerField(
        default=24,
        verbose_name='Generation Interval (Hours)'
    )
    last_generated = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Generated'
    )
    
    class Meta:
        db_table = 'user_auth_admin_code'
        verbose_name = 'Admin Code'
        verbose_name_plural = 'Admin Codes'
    
    def __str__(self):
        return f"{self.code} ({self.description})"
    
    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.current_uses >= self.max_uses:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
    
    def use_code(self):
        if self.is_valid:
            self.current_uses += 1
            # 자동 생성 코드인 경우 사용 즉시 새 코드 생성
            if self.auto_generate:
                self.code = self.generate_code()
                self.last_generated = timezone.now()
                self.current_uses = 0  # 사용 횟수 초기화
            self.save()
            return True
        return False
    
    @classmethod
    def generate_code(cls, length=8):
        """Generate secure random code"""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def should_regenerate(self):
        """Check if code regeneration is needed (only when unused)"""
        if not self.auto_generate:
            return False
        if not self.last_generated:
            return True
        # Time-based regeneration only when unused
        if self.current_uses == 0:
            next_generation = self.last_generated + timedelta(hours=self.generation_interval_hours)
            return timezone.now() >= next_generation
        return False
    
    def regenerate_code(self):
        """Regenerate with new code"""
        if self.should_regenerate():
            self.code = self.generate_code()
            self.last_generated = timezone.now()
            self.current_uses = 0
            self.save()
            return True
        return False
    
    def create_new_auto_code(self):
        """Create completely new auto-generated code (delete existing codes)"""
        if self.auto_generate:
            # Deactivate existing auto-generated codes
            AdminCode.objects.filter(auto_generate=True).update(is_active=False)
            
            # Generate new code
            self.code = self.generate_code()
            self.last_generated = timezone.now()
            self.current_uses = 0
            self.is_active = True
            self.save()
            return True
        return False
    
    @classmethod
    def get_current_code(cls):
        """Return currently active auto-generated code"""
        auto_codes = cls.objects.filter(auto_generate=True, is_active=True)
        for code in auto_codes:
            if code.should_regenerate():
                code.regenerate_code()
        
        # is_valid is a property, so filter in Python
        for code in auto_codes:
            if code.is_valid:
                return code
        return None
