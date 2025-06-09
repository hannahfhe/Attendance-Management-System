# ===============================================
# accounts/admin.py
# ===============================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin"""
    
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'phone', 'department', 'role', 'manager')
        }),
        ('Work Schedule', {
            'fields': ('work_start_time', 'work_end_time')
        }),
        ('Profile', {
            'fields': ('profile_picture',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'phone', 'department', 'role', 'first_name', 'last_name')
        }),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'employee_id', 'department', 'role', 'is_active')
    list_filter = ('role', 'department', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    ordering = ('employee_id',)



