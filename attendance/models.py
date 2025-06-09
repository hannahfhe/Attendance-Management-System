

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()

class AttendanceRecord(models.Model):
    """Model to track daily attendance records"""
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    

    total_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    break_time = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)  # in hours
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    is_late = models.BooleanField(default=False)
    late_by_minutes = models.IntegerField(default=0)
    

    check_in_location = models.CharField(max_length=255, blank=True)
    check_out_location = models.CharField(max_length=255, blank=True)
    
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_record'
        unique_together = ('user', 'date')
        ordering = ['-date']
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
    
    def __str__(self):
        return f"{self.user.full_name} - {self.date} ({self.status})"
    
    def calculate_hours(self):
        """Calculate total working hours"""
        if self.check_in_time and self.check_out_time:
        
            check_in = datetime.combine(self.date, self.check_in_time)
            check_out = datetime.combine(self.date, self.check_out_time)
            
      
            if check_out < check_in:
                check_out += timedelta(days=1)
            
            total_time = check_out - check_in
            hours = total_time.total_seconds() / 3600
            
    
            self.total_hours = round(hours - float(self.break_time), 2)
            
           
            standard_hours = 8.0
            if self.total_hours > standard_hours:
                self.overtime_hours = round(self.total_hours - standard_hours, 2)
            else:
                self.overtime_hours = 0.00
    
    def check_late_status(self):
        """Check if employee is late"""
        if self.check_in_time and self.user.work_start_time:
            work_start = datetime.combine(self.date, self.user.work_start_time)
            actual_checkin = datetime.combine(self.date, self.check_in_time)
            
            if actual_checkin > work_start:
                self.is_late = True
                late_duration = actual_checkin - work_start
                self.late_by_minutes = int(late_duration.total_seconds() / 60)
                if self.status == 'present':
                    self.status = 'late'
    
    def save(self, *args, **kwargs):
      
        self.calculate_hours()
        self.check_late_status()
        super().save(*args, **kwargs)


class CheckInOut(models.Model):
    """Model to track individual check-in/check-out events"""
    
    EVENT_CHOICES = [
        ('check_in', 'Check In'),
        ('check_out', 'Check Out'),
        ('break_start', 'Break Start'),
        ('break_end', 'Break End'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checkin_events')
    event_type = models.CharField(max_length=15, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'checkin_out'
        ordering = ['-timestamp']
        verbose_name = 'Check In/Out Event'
        verbose_name_plural = 'Check In/Out Events'
    
    def __str__(self):
        return f"{self.user.full_name} - {self.event_type} at {self.timestamp}"

