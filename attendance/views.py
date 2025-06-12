
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q,Sum
from django.utils import timezone
from django.contrib import messages
from .models import AttendanceRecord, CheckInOut
from accounts.models import User
from datetime import datetime, date, timedelta
import csv

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import date, datetime

@login_required
def attendance_dashboard(request):
    """Simple attendance dashboard with server-side rendering and pagination"""
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
        
     
        records = records.order_by('-date', 'user__first_name')
        
    
        paginator = Paginator(records, 25)  
        page = request.GET.get('page')
        
        try:
            records = paginator.page(page)
        except PageNotAnInteger:
           
            records = paginator.page(1)
        except EmptyPage:
        
            records = paginator.page(paginator.num_pages)
        
      
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
       
        user_records = AttendanceRecord.objects.filter(user=user).order_by('-date')
        
        paginator = Paginator(user_records, 10)  
        page = request.GET.get('page')
        
        try:
            records = paginator.page(page)
        except PageNotAnInteger:
            records = paginator.page(1)
        except EmptyPage:
            records = paginator.page(paginator.num_pages)
            
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
    """View all attendance records for the user with filtering"""
    
    # Get filter parameters from request
    month_filter = request.GET.get('month', '')
    year_filter = request.GET.get('year', '')
    status_filter = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    # Base queryset
    records = AttendanceRecord.objects.filter(user=request.user)
    
    # Apply filters
    if month_filter:
        records = records.filter(date__month=int(month_filter))
    if year_filter:
        records = records.filter(date__year=int(year_filter))
    if status_filter:
        if status_filter == 'present':
            records = records.filter(Q(status='present') | Q(status='late'))
        else:
            records = records.filter(status=status_filter)
    
    # Order by date (most recent first)
    records = records.order_by('-date')
    
    # Calculate summary statistics for filtered records
    summary_stats = {
        'total_present': records.filter(Q(status='present') | Q(status='late')).count(),
        'total_absent': records.filter(status='absent').count(),
        'total_late': records.filter(is_late=True).count(),
        'total_hours': records.aggregate(Sum('total_hours'))['total_hours__sum'] or 0,
    }
    
    # Pagination
    paginator = Paginator(records, 20)  # 20 records per page
    page_obj = paginator.get_page(page)
    
    # Get current date for default filters
    current_date = date.today()
    
    # Generate year options (current year and previous 2 years)
    year_options = [current_date.year - i for i in range(3)]
    
    # Month options
    month_options = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    context = {
        'page_obj': page_obj,
        'summary_stats': summary_stats,
        'month_filter': month_filter,
        'year_filter': year_filter,
        'status_filter': status_filter,
        'year_options': year_options,
        'month_options': month_options,
        'current_month': current_date.month,
        'current_year': current_date.year,
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