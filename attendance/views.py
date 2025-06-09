
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from .models import AttendanceRecord, CheckInOut
from accounts.models import User
from datetime import datetime, date, timedelta
import csv

@login_required
def attendance_dashboard(request):
    """Simple attendance dashboard with server-side rendering only"""
    today = date.today()
    user = request.user
    

    today_record = AttendanceRecord.objects.filter(
        user=user, 
        date=today
    ).first()
    
    if user.is_staff:
    
        records = AttendanceRecord.objects.select_related('user').all()
        
     
        search = request.GET.get('search', '').strip()
        department = request.GET.get('department', '').strip()
        status = request.GET.get('status', '').strip()
        date_filter = request.GET.get('date', '').strip()
        
        if search:
            records = records.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        if department:
       
            if hasattr(User, 'department'):
                records = records.filter(user__department=department)
            else:
                records = records.filter(user__groups__name=department)
        
        if status:
            records = records.filter(status=status)
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                records = records.filter(date=filter_date)
            except ValueError:
                pass
        
     
        records = records.order_by('-date', 'user__first_name')[:100]
        
      
        present_count = AttendanceRecord.objects.filter(
            status='present', date=today
        ).count()
        late_count = AttendanceRecord.objects.filter(
            status='late', date=today
        ).count()
        absent_count = AttendanceRecord.objects.filter(
            status='absent', date=today
        ).count()
        total_employees = User.objects.filter(is_active=True).count()
        
    else:
        # Regular user view
        records = AttendanceRecord.objects.filter(user=user).order_by('-date')[:10]
        present_count = late_count = absent_count = total_employees = 0
    
    context = {
        'today_record': today_record,
        'records': records,
        'present': present_count,
        'late': late_count,
        'absent': absent_count,
        'total_employees': total_employees,
        'current_filters': {
            'search': request.GET.get('search', ''),
            'department': request.GET.get('department', ''),
            'status': request.GET.get('status', ''),
            'date': request.GET.get('date', ''),
        }
    }
    return render(request, 'attendance/dashboard.html', context)

@login_required
def attendance_records(request):
    """View all attendance records for the user"""
    records = AttendanceRecord.objects.filter(
        user=request.user
    ).order_by('-date')[:50]
    
    context = {
        'records': records,
    }
    return render(request, 'attendance/records.html', context)

@login_required
def check_in_view(request):
    """Handle check-in"""
    if request.method == 'POST':
        today = date.today()
        current_time = timezone.now().time()
        
      
        existing_record = AttendanceRecord.objects.filter(
            user=request.user,
            date=today
        ).first()
        
        if existing_record and existing_record.check_in_time:
            messages.warning(request, 'You have already checked in today.')
            return redirect('attendance:dashboard')
        
     
        if existing_record:
            existing_record.check_in_time = current_time
            existing_record.status = 'present'
            existing_record.save()
        else:
            AttendanceRecord.objects.create(
                user=request.user,
                date=today,
                check_in_time=current_time,
                status='present'
            )
        
      
        CheckInOut.objects.create(
            user=request.user,
            event_type='check_in',
            timestamp=timezone.now(),
            ip_address=get_client_ip(request)
        )
        
        messages.success(
            request, 
            f'Checked in successfully at {current_time.strftime("%H:%M")}'
        )
    
    return redirect('attendance:dashboard')

@login_required
def check_out_view(request):
    """Handle check-out"""
    if request.method == 'POST':
        today = date.today()
        current_time = timezone.now().time()
        
      
        record = AttendanceRecord.objects.filter(
            user=request.user,
            date=today
        ).first()
        
        if not record or not record.check_in_time:
            messages.error(request, 'Please check in first.')
            return redirect('attendance:dashboard')
        
        if record.check_out_time:
            messages.warning(request, 'You have already checked out today.')
            return redirect('attendance:dashboard')
        
       
        record.check_out_time = current_time
        record.save()
        
      
        CheckInOut.objects.create(
            user=request.user,
            event_type='check_out',
            timestamp=timezone.now(),
            ip_address=get_client_ip(request)
        )
        
        messages.success(
            request, 
            f'Checked out successfully at {current_time.strftime("%H:%M")}. '
            f'Total hours: {record.total_hours}'
        )
    
    return redirect('attendance:dashboard')

@login_required
def admin_checkout(request, record_id):
    """Admin force checkout"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('attendance:dashboard')
    
    if request.method == 'POST':
        try:
            record = AttendanceRecord.objects.get(id=record_id)
            
            if record.check_out_time:
                messages.warning(request, 'Employee already checked out.')
                return redirect('attendance:dashboard')
            
            if not record.check_in_time:
                messages.error(request, 'Employee has not checked in yet.')
                return redirect('attendance:dashboard')
            
         
            current_time = timezone.now().time()
            record.check_out_time = current_time
            record.save()
            
         
            CheckInOut.objects.create(
                user=record.user,
                event_type='check_out',
                timestamp=timezone.now(),
                notes=f'Force checkout by admin: {request.user.username}'
            )
            
            messages.success(
                request, 
                f'Successfully checked out {record.user.get_full_name()} at {current_time.strftime("%H:%M")}'
            )
            
        except AttendanceRecord.DoesNotExist:
            messages.error(request, 'Attendance record not found.')
    
    return redirect('attendance:dashboard')

@login_required
def employee_detail(request, employee_id):
    """View employee details (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('attendance:dashboard')
    
    try:
        employee = User.objects.get(id=employee_id)
        records = AttendanceRecord.objects.filter(
            user=employee
        ).order_by('-date')[:30]  
        
        context = {
            'employee': employee,
            'records': records,
        }
        return render(request, 'attendance/employee_detail.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'Employee not found.')
        return redirect('attendance:dashboard')

@login_required
def export_data(request):
    """Export attendance data to CSV"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('attendance:dashboard')
    
   
    records = AttendanceRecord.objects.select_related('user').all()
    
    search = request.GET.get('search', '').strip()
    department = request.GET.get('department', '').strip()
    status = request.GET.get('status', '').strip()
    date_filter = request.GET.get('date', '').strip()
    
    if search:
        records = records.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    if department:
        if hasattr(User, 'department'):
            records = records.filter(user__department=department)
        else:
            records = records.filter(user__groups__name=department)
    
    if status:
        records = records.filter(status=status)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            records = records.filter(date=filter_date)
        except ValueError:
            pass
    

    response = HttpResponse(
        content_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="attendance_export_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
        },
    )
    
    writer = csv.writer(response)
    
 
    writer.writerow([
        'Employee ID', 'Employee Name', 'Email', 'Department',
        'Date', 'Day', 'Check In', 'Check Out',
        'Total Hours', 'Status', 'Late', 'Late By (minutes)'
    ])
    

    for record in records.order_by('-date'):
        full_name = f"{record.user.first_name} {record.user.last_name}".strip()
        if not full_name:
            full_name = record.user.username
        
        department = getattr(record.user, 'department', 'N/A') or 'N/A'
        
        writer.writerow([
            record.user.id,
            full_name,
            record.user.email,
            department,
            record.date.strftime('%Y-%m-%d'),
            record.date.strftime('%A'),
            record.check_in_time.strftime('%H:%M') if record.check_in_time else '',
            record.check_out_time.strftime('%H:%M') if record.check_out_time else '',
            record.total_hours,
            record.get_status_display(),
            'Yes' if record.is_late else 'No',
            record.late_by_minutes,
        ])
    
    return response

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip