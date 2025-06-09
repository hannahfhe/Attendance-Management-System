# ===============================================
# attendance/admin.py
# ===============================================

from django.contrib import admin
from .models import AttendanceRecord, CheckInOut

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'check_in_time', 'check_out_time', 'total_hours', 'status', 'is_late')
    list_filter = ('status', 'is_late', 'date', 'user__department')
    search_fields = ('user__first_name', 'user__last_name', 'user__employee_id')
    date_hierarchy = 'date'
    readonly_fields = ('total_hours', 'overtime_hours', 'late_by_minutes')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date', 'status')
        }),
        ('Time Tracking', {
            'fields': ('check_in_time', 'check_out_time', 'break_time')
        }),
        ('Calculated Fields', {
            'fields': ('total_hours', 'overtime_hours', 'is_late', 'late_by_minutes'),
            'classes': ('collapse',)
        }),
        ('Location & Notes', {
            'fields': ('check_in_location', 'check_out_location', 'notes'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CheckInOut)
class CheckInOutAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'timestamp', 'location')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('user__first_name', 'user__last_name')
    date_hierarchy = 'timestamp'

