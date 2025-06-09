


from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Report(models.Model):
    """Generated reports storage"""
    
    REPORT_TYPES = [
        ('daily', 'Daily Attendance'),
        ('monthly', 'Monthly Summary'),
        ('employee', 'Employee Report'),
        ('department', 'Department Report'),
        ('leave', 'Leave Report'),
        ('overtime', 'Overtime Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    department = models.CharField(max_length=20, blank=True)
    
  
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    

    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    file_size = models.IntegerField(default=0)  # in bytes
    
    class Meta:
        db_table = 'report'
        ordering = ['-generated_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
    
    def __str__(self):
        return f"{self.title} - {self.generated_at.strftime('%Y-%m-%d')}"