from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from user_auth.models import User, AdminCode

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'name')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'name', 'role')}),
        ('Admin code info', {'fields': ('admin_code_used',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'name', 'password1', 'password2', 'role'),
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Set user deletion permissions"""
        # Only superusers can delete all users
        if not request.user.is_superuser:
            return False
        
        # Superusers cannot delete themselves
        if obj and obj.is_superuser and obj == request.user:
            return False
            
        return True
    
    def has_change_permission(self, request, obj=None):
        """Restrict superuser permission changes"""
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

@admin.register(AdminCode)
class AdminCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'is_active', 'auto_generate', 'current_uses', 'max_uses', 'expires_at', 'created_at')
    list_filter = ('is_active', 'auto_generate', 'created_at', 'expires_at')
    search_fields = ('code', 'description')
    readonly_fields = ('current_uses', 'created_at', 'last_generated')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('code', 'description')}),
        ('Auto Generation', {
            'fields': ('auto_generate', 'generation_interval_hours', 'last_generated'),
            'description': 'Auto-generation settings - Regenerate immediately when used, or at set intervals when unused'
        }),
        ('Usage settings', {'fields': ('is_active', 'max_uses', 'current_uses')}),
        ('Expiration', {'fields': ('expires_at',)}),
        ('Metadata', {'fields': ('created_at',)}),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make auto-generated codes non-editable"""
        if obj and obj.auto_generate:
            return self.readonly_fields + ('code',)
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        """Handle admin code saving"""
        # For auto-generated codes
        if obj.auto_generate and not obj.code:
            obj.code = AdminCode.generate_code()
        
        # For manual codes - security enhancement
        if not obj.auto_generate and not obj.code:
            # Auto-generate if admin doesn't input code directly
            obj.code = AdminCode.generate_code()
            self.message_user(request, f"Complex code auto-generated for security: {obj.code}")
        
        # Set default expiration (7 days) if not set
        if not obj.expires_at:
            from datetime import timedelta
            from django.utils import timezone
            obj.expires_at = timezone.now() + timedelta(days=7)
        
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        """Prevent auto-generated code deletion (superusers only)"""
        if obj and obj.auto_generate:
            # Only superusers can delete auto-generated codes
            return request.user.is_superuser
        return super().has_delete_permission(request, obj)
