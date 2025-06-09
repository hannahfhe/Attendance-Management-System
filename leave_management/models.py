# ===============================================
# leave_management/models.py
# ===============================================

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

User = get_user_model()

class LeaveType(models.Model):
    """Different types of leaves available"""
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    max_days_per_year = models.IntegerField(default=30)
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'leave_type'
        verbose_name = 'Leave Type'
        verbose_name_plural = 'Leave Types'


class LeaveRequest(models.Model):
    """Employee leave requests"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    LEAVE_CHOICES = [
    ('sick', 'Sick'),
    ('vacation', 'Vacation'),
]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(
    max_length=20,
    choices=LEAVE_CHOICES,
)
    
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField()
    
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Approval workflow
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Supporting documents
    supporting_document = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'leave_request'
        ordering = ['-created_at']
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
    
    def __str__(self):
        return f"{self.user.full_name} - {self.leave_type.name} ({self.start_date} to {self.end_date})"
    
    def calculate_total_days(self):
        """Calculate total leave days excluding weekends"""
        if self.start_date and self.end_date:
            total_days = 0
            current_date = self.start_date
            
            while current_date <= self.end_date:
                # Skip weekends (Saturday=5, Sunday=6)
                if current_date.weekday() < 5:
                    total_days += 1
                current_date += timezone.timedelta(days=1)
            
            self.total_days = total_days
    
    def save(self, *args, **kwargs):
        self.calculate_total_days()
        super().save(*args, **kwargs)
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'


class LeaveBalance(models.Model):
    """Track leave balances for each employee"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField(default=False, )
    
    allocated_days = models.IntegerField(default=0)
    used_days = models.IntegerField(default=0)
    remaining_days = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'leave_balance'
        unique_together = ('user', 'leave_type', 'year')
        verbose_name = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'
    
    def __str__(self):
        return f"{self.user.full_name} - {self.leave_type.name} ({self.year})"
    
    def update_balance(self):
        """Update remaining days"""
        self.remaining_days = self.allocated_days - self.used_days
    
    def save(self, *args, **kwargs):
        self.update_balance()
        super().save(*args, **kwargs)

