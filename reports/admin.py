
from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'format', 'generated_by', 'generated_at', 'file_size')
    list_filter = ('report_type', 'format', 'generated_at', 'department')
    search_fields = ('title', 'generated_by__first_name', 'generated_by__last_name')
    date_hierarchy = 'generated_at'
    readonly_fields = ('file_size', 'generated_at')