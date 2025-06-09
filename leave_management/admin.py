# ===============================================
# leave_management/admin.py
# ===============================================

from django.contrib import admin
from .models import LeaveType, LeaveRequest, LeaveBalance

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_days_per_year', 'requires_approval', 'is_active')
    list_filter = ('requires_approval', 'is_active')
    search_fields = ('name',)

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'total_days', 'status', 'created_at')
    list_filter = ('status', 'leave_type', 'start_date', 'user__department')
    search_fields = ('user__first_name', 'user__last_name', 'reason')
    date_hierarchy = 'start_date'
    readonly_fields = ('total_days', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'leave_type', 'start_date', 'end_date', 'total_days', 'reason')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Documents', {
            'fields': ('supporting_document',)
        }),
    )

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'year', 'allocated_days', 'used_days', 'remaining_days')
    list_filter = ('year', 'leave_type', 'user__department')
    search_fields = ('user__first_name', 'user__last_name')


