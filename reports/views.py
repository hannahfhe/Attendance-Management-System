
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse,  Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from .models import Report
from attendance.models import AttendanceRecord
from leave_management.models import LeaveRequest
from accounts.models import User
from datetime import datetime, date, timedelta
import json
from accounts.decorators import hr_required, admin_required
from django.core.files.base import ContentFile
from datetime import date, datetime, timedelta
import io
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
@hr_required

@login_required
def reports_dashboard(request):
    """Reports dashboard with statistics"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    today = timezone.now().date()
    
 
    total_employees = User.objects.filter(is_active=True).count()
    

    today_attendance = AttendanceRecord.objects.filter(date=today)
    present_today = today_attendance.filter(status__in=['present', 'late']).count()
    

    pending_leaves = LeaveRequest.objects.filter(status='pending').count()

    total_reports = Report.objects.count()
    
  
    recent_reports = Report.objects.select_related('generated_by').order_by('-generated_at')[:10]
    
    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'pending_leaves': pending_leaves,
        'total_reports': total_reports,
        'recent_reports': recent_reports,
        'page_title': 'Reports Dashboard'
    }
    
    return render(request, 'reports/dashboard.html', context)

@login_required  
def analytics_dashboard(request):
    """Detailed analytics dashboard"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    

    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
  
    daily_stats = []
    for i in range(14):
        check_date = today - timedelta(days=i)
        day_records = AttendanceRecord.objects.filter(date=check_date)
        present = day_records.filter(status__in=['present', 'late']).count()
        absent = day_records.filter(status='absent').count()
        late = day_records.filter(is_late=True).count()
        total = day_records.count()
        
        daily_stats.append({
            'date': check_date,
            'present': present,
            'absent': absent,
            'late': late,
            'total': total,
            'percentage': round((present / total * 100) if total > 0 else 0, 1)
        })
    
    daily_stats.reverse()  
    

    departments = User.objects.filter(is_active=True).values_list('department', flat=True).distinct()
    department_stats = []
    
    for dept in departments:
        if dept:  
            dept_employees = User.objects.filter(department=dept, is_active=True)
            dept_records = AttendanceRecord.objects.filter(
                user__in=dept_employees,
                date__gte=last_30_days
            )
            
            total_possible = dept_employees.count() * 30  
            present_count = dept_records.filter(status__in=['present', 'late']).count()
            percentage = round((present_count / total_possible * 100) if total_possible > 0 else 0, 1)
            
            department_stats.append({
                'department': dept,
                'percentage': percentage,
                'present_count': present_count,
                'total_possible': total_possible
            })

    total_present = sum(day['present'] for day in daily_stats)
    total_absent = sum(day['absent'] for day in daily_stats)
    total_late = sum(day['late'] for day in daily_stats)
    avg_attendance = round(sum(dept['percentage'] for dept in department_stats) / len(department_stats) if department_stats else 0, 1)
    
    context = {
        'daily_stats': daily_stats,
        'department_stats': department_stats,
        'summary_stats': {
            'total_present': total_present,
            'total_absent': total_absent,
            'total_late': total_late,
            'avg_attendance': avg_attendance
        },
        'page_title': 'Analytics Dashboard'
    }
    
    return render(request, 'reports/analytics_dashboard.html', context)


@login_required
def generate_report(request):
    """Report generation form and processing"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        # Get form data
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        format_type = request.POST.get('format', 'pdf')
        employee_filter = request.POST.get('employee_filter')
        department_filter = request.POST.get('department_filter')
        include_charts = request.POST.get('include_charts') == '1'
        include_summary = request.POST.get('include_summary') == '1'
        include_details = request.POST.get('include_details') == '1'
        email_report = request.POST.get('email_report') == '1'
        
        # Validate dates
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('reports:generate')
        
        if start_date_obj > end_date_obj:
            messages.error(request, 'Start date cannot be after end date.')
            return redirect('reports:generate')
        
        # Generate report title
        report_title = f"{report_type.title()} Report - {start_date_obj.strftime('%Y-%m-%d')} to {end_date_obj.strftime('%Y-%m-%d')}"
        
        # Create report instance
        report = Report.objects.create(
            title=report_title,
            report_type=report_type,
            format=format_type,
            start_date=start_date_obj,
            end_date=end_date_obj,
            department=department_filter or '',
            generated_by=request.user
        )
        
        try:
            # Generate the actual report file based on type and format
            
            if report_type == 'leave':
                file_content = generate_leave_report(
                    start_date_obj, end_date_obj, format_type,
                    employee_filter, department_filter, include_summary, include_details
                )
            elif report_type == 'employee':
                file_content = generate_employee_report(
                    start_date_obj, end_date_obj, format_type,
                    employee_filter, department_filter, include_summary, include_details
                )
            elif report_type == 'department':
                file_content = generate_department_report(
                    start_date_obj, end_date_obj, format_type,
                    department_filter, include_summary, include_details
                )
            else:
                file_content = generate_summary_report(
                    start_date_obj, end_date_obj, format_type,
                    employee_filter, department_filter, include_summary, include_details
                )
            
            # Save file to report instance
            filename = f"{report_type}_report_{start_date_obj}_{end_date_obj}.{format_type}"
            report.file.save(filename, ContentFile(file_content), save=True)
            report.file_size = len(file_content)
            report.save()
            
            messages.success(request, f'{report_type.title()} report generated successfully! <a href="{report.file.url}" class="underline">Download Report</a>')
            
            # If email is requested, send the report (implement email functionality as needed)
            if email_report:
                # TODO: Implement email functionality
                messages.info(request, 'Email functionality will be implemented soon.')
            
        except Exception as e:
            # If report generation fails, delete the report instance
            report.delete()
            messages.error(request, f'Error generating report: {str(e)}')
            
        return redirect('reports:dashboard')
    
    # GET request - show form
    employees = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    departments = User.objects.filter(is_active=True).values_list('department', flat=True).distinct()
    departments = [dept for dept in departments if dept]  # Remove None values
    
    context = {
        'employees': employees,
        'departments': departments,
        'page_title': 'Generate Report'
    }
    
    return render(request, 'reports/generate_report.html', context)



# Similar functions for other report types (leave, employee, department, summary)
def generate_leave_report(start_date, end_date, format_type, employee_filter=None, department_filter=None, include_summary=True, include_details=True):
    """Generate leave report - implement similar to attendance report"""
    # Implementation similar to attendance report but for leave data
    return b"Leave report content"  # Placeholder

def generate_employee_report(start_date, end_date, format_type, employee_filter=None, department_filter=None, include_summary=True, include_details=True):
    """Generate employee report - implement similar to attendance report"""
    # Implementation for employee-specific reports
    return b"Employee report content"  # Placeholder

def generate_department_report(start_date, end_date, format_type, department_filter=None, include_summary=True, include_details=True):
    """Generate department report - implement similar to attendance report"""
    # Implementation for department-specific reports
    return b"Department report content"  # Placeholder

def generate_summary_report(start_date, end_date, format_type, employee_filter=None, department_filter=None, include_summary=True, include_details=True):
    """Generate summary report - implement similar to attendance report"""
    # Implementation for summary reports
    return b"Summary report content"  # Placeholder

@login_required
def download_report(request, report_id):
    """Download a generated report"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    report = get_object_or_404(Report, id=report_id)
    
    if not report.file:
        raise Http404("Report file not found")
    
    response = HttpResponse(
        report.file.read(),
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{report.file.name}"'
    return response

@login_required
def delete_report(request, report_id):
    """Delete a generated report"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    report = get_object_or_404(Report, id=report_id)
    
    if request.method == 'POST':
        # Delete the file if it exists
        if report.file:
            report.file.delete()
        
        report.delete()
        messages.success(request, 'Report deleted successfully.')
    
    return redirect('reports:dashboard')
@login_required
def attendance_report(request):
    """Attendance report view"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department = request.GET.get('department')
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = date.today().replace(day=1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Build query
    query = Q(date__range=[start_date, end_date])
    if department:
        query &= Q(user__department=department)
    
    # Get attendance records
    records = AttendanceRecord.objects.filter(query).select_related('user')
    
    # Calculate statistics
    total_records = records.count()
    present_count = records.filter(status__in=['present', 'late']).count()
    absent_count = records.filter(status='absent').count()
    late_count = records.filter(is_late=True).count()
    
    # Group by employee
    employee_stats = {}
    for record in records:
        emp_id = record.user.id
        if emp_id not in employee_stats:
            employee_stats[emp_id] = {
                'employee': record.user,
                'present': 0,
                'absent': 0,
                'late': 0,
                'total_hours': 0
            }
        
        if record.status in ['present', 'late']:
            employee_stats[emp_id]['present'] += 1
        elif record.status == 'absent':
            employee_stats[emp_id]['absent'] += 1
        
        if record.is_late:
            employee_stats[emp_id]['late'] += 1
        
        employee_stats[emp_id]['total_hours'] += float(record.total_hours)
    
    context = {
        'records': records,
        'employee_stats': employee_stats.values(),
        'start_date': start_date,
        'end_date': end_date,
        'department': department,
        'stats': {
            'total_records': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
        },
        'page_title': 'Attendance Report'
    }
    return render(request, 'reports/attendance_report.html', context)

@login_required
def leave_report(request):
    """Leave report view"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department = request.GET.get('department')
    status = request.GET.get('status')
    
    # Default to current year if no dates provided
    if not start_date:
        start_date = date.today().replace(month=1, day=1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Build query
    query = Q(start_date__range=[start_date, end_date])
    if department:
        query &= Q(user__department=department)
    if status:
        query &= Q(status=status)
    
    # Get leave requests
    leave_requests = LeaveRequest.objects.filter(query).select_related('user', 'leave_type')
    
    # Calculate statistics
    total_requests = leave_requests.count()
    approved_count = leave_requests.filter(status='approved').count()
    pending_count = leave_requests.filter(status='pending').count()
    rejected_count = leave_requests.filter(status='rejected').count()
    
    # Group by leave type
    leave_type_stats = leave_requests.values('leave_type__name').annotate(
        count=Count('id'),
        total_days=Sum('total_days')
    )
    
    context = {
        'leave_requests': leave_requests,
        'leave_type_stats': leave_type_stats,
        'start_date': start_date,
        'end_date': end_date,
        'department': department,
        'status': status,
        'stats': {
            'total_requests': total_requests,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
        },
        'page_title': 'Leave Report'
    }
    return render(request, 'reports/leave_report.html', context)

@login_required
def employee_report(request):
    """Employee-wise report"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    # Get all active employees for dropdown
    employees = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    # Get form data
    selected_employee_id = request.GET.get('employee')
    selected_month = request.GET.get('month', str(date.today().month))
    selected_year = request.GET.get('year', str(date.today().year))
    
    # Initialize context
    context = {
        'employees': employees,
        'selected_employee_id': selected_employee_id,
        'selected_month': int(selected_month),
        'selected_year': int(selected_year),
        'months': [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ],
        'years': [2024, 2025, 2026],
        'page_title': 'Employee Report',
        'show_report': False
    }
    
    # If employee is selected, generate report
    if selected_employee_id:
        try:
            selected_employee = User.objects.get(id=selected_employee_id, is_active=True)
            
            # Get attendance records for selected month/year
            attendance_records = AttendanceRecord.objects.filter(
                user=selected_employee,
                date__month=int(selected_month),
                date__year=int(selected_year)
            ).order_by('-date')
            
            # Calculate metrics
            present_days = attendance_records.filter(status__in=['present', 'late']).count()
            absent_days = attendance_records.filter(status='absent').count()
            late_days = attendance_records.filter(is_late=True).count()
            total_hours = attendance_records.aggregate(total=Sum('total_hours'))['total'] or 0
            
            # Calculate attendance rate
            total_working_days = attendance_records.count()
            attendance_rate = (present_days / total_working_days * 100) if total_working_days > 0 else 0
            
            # Calculate punctuality rate
            punctuality_rate = ((present_days - late_days) / present_days * 100) if present_days > 0 else 0
            
            # Calculate average hours per day
            avg_hours_per_day = (total_hours / present_days) if present_days > 0 else 0
            
            # Get leave requests for the year
            leave_requests = LeaveRequest.objects.filter(
                user=selected_employee,
                status='approved',
                start_date__year=int(selected_year)
            )
            total_leave_days = leave_requests.aggregate(total=Sum('total_days'))['total'] or 0
            
            # Update context with report data
            context.update({
                'show_report': True,
                'selected_employee': selected_employee,
                'attendance_records': attendance_records[:15],  # Show last 15 records
                'metrics': {
                    'attendance_rate': round(attendance_rate, 1),
                    'avg_hours_per_day': round(avg_hours_per_day, 1),
                    'punctuality_rate': round(punctuality_rate, 1),
                    'productivity_rate': round(attendance_rate * 0.98, 1),  # Simple calculation
                    'present_days': present_days,
                    'absent_days': absent_days,
                    'late_days': late_days,
                    'total_hours': round(total_hours, 1),
                    'total_leave_days': total_leave_days,
                }
            })
            
        except User.DoesNotExist:
            messages.error(request, 'Selected employee not found.')
    
    return render(request, 'reports/employee_report.html', context)
@login_required
def department_report(request):
    """Department-wise report"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    # Get all departments
    departments = User.objects.values_list('department', flat=True).distinct().exclude(department='').exclude(department__isnull=True)
    
    department_data = []
    current_month = date.today().month
    current_year = date.today().year
    
    # Initialize totals
    total_employees = 0
    total_leaves = 0
    total_attendance_rates = []
    
    for dept in departments:
        # Get employees in this department
        dept_employees = User.objects.filter(department=dept, is_active=True)
        dept_employee_count = dept_employees.count()
        total_employees += dept_employee_count
        
        # Attendance stats
        attendance_records = AttendanceRecord.objects.filter(
            user__department=dept,
            date__month=current_month,
            date__year=current_year
        )
        
        total_present = attendance_records.filter(status__in=['present', 'late']).count()
        total_absent = attendance_records.filter(status='absent').count()
        total_late = attendance_records.filter(is_late=True).count()
        avg_hours = attendance_records.aggregate(avg=Avg('total_hours'))['avg'] or 0
        
    
        dept_total_leaves = LeaveRequest.objects.filter(
            user__department=dept,
            status='approved',
            start_date__year=current_year
        ).aggregate(total=Sum('total_days'))['total'] or 0
        total_leaves += dept_total_leaves
        
    
        attendance_rate = round((total_present / (total_present + total_absent)) * 100, 2) if (total_present + total_absent) > 0 else 0
        total_attendance_rates.append(attendance_rate)
        
        department_data.append({
            'department': dept,
            'total_employees': dept_employee_count,
            'total_present': total_present,
            'total_absent': total_absent,
            'total_late': total_late,
            'avg_hours': round(float(avg_hours), 2),
            'total_leaves': dept_total_leaves,
            'attendance_rate': attendance_rate
        })
    

    avg_attendance_rate = round(sum(total_attendance_rates) / len(total_attendance_rates), 1) if total_attendance_rates else 0
    
    context = {
        'department_data': department_data,
        'total_employees': total_employees,
        'total_leaves': total_leaves,
        'avg_attendance_rate': avg_attendance_rate,
        'total_departments': len(departments),
        'current_month': current_month,
        'current_year': current_year,
        'page_title': 'Department Report'
    }
    return render(request, 'reports/department_report.html', context)
@login_required
def download_report(request, report_id):
    """Download generated report"""
    if not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    report = get_object_or_404(Report, id=report_id)
    
    if report.file:
        response = HttpResponse(report.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{report.file.name}"'
        return response
    else:
        messages.error(request, 'Report file not found.')
        return redirect('reports:dashboard')


@login_required
@csrf_exempt
def generate_report_api(request):
    """API endpoint to generate reports"""
    if not request.user.is_admin_or_hr:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        report = Report.objects.create(
            title=data.get('title', f"Report - {timezone.now().strftime('%Y-%m-%d')}"),
            report_type=data['report_type'],
            format=data.get('format', 'pdf'),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            department=data.get('department', ''),
            generated_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Report generated successfully',
            'report_id': report.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def reports_list_api(request):
    """API endpoint to get list of reports"""
    if not request.user.is_admin_or_hr:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    reports = Report.objects.filter(
        generated_by=request.user
    ).order_by('-generated_at')
    
    data = []
    for report in reports:
        data.append({
            'id': report.id,
            'title': report.title,
            'report_type': report.report_type,
            'format': report.format,
            'start_date': report.start_date.strftime('%Y-%m-%d') if report.start_date else None,
            'end_date': report.end_date.strftime('%Y-%m-%d') if report.end_date else None,
            'department': report.department,
            'generated_at': report.generated_at.isoformat(),
            'file_size': report.file_size
        })
    
    return JsonResponse({'reports': data})

@login_required
def attendance_data_api(request):
    """API endpoint for attendance data (for charts/graphs)"""
    if not request.user.is_admin_or_hr:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get last 30 days data
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    daily_stats = []
    current_date = start_date
    
    while current_date <= end_date:
        day_records = AttendanceRecord.objects.filter(date=current_date)
        present_count = day_records.filter(status__in=['present', 'late']).count()
        absent_count = day_records.filter(status='absent').count()
        late_count = day_records.filter(is_late=True).count()
        
        daily_stats.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'total': present_count + absent_count
        })
        
        current_date += timedelta(days=1)
    
 
    dept_stats = []
    departments = User.objects.values_list('department', flat=True).distinct().exclude(department='')
    
    for dept in departments:
        dept_present = AttendanceRecord.objects.filter(
            user__department=dept,
            date=end_date,
            status__in=['present', 'late']
        ).count()
        
        dept_total = User.objects.filter(department=dept, is_active=True).count()
        
        dept_stats.append({
            'department': dept,
            'present': dept_present,
            'total': dept_total,
            'percentage': round((dept_present / dept_total) * 100, 2) if dept_total > 0 else 0
        })
    
    return JsonResponse({
        'daily_stats': daily_stats,
        'department_stats': dept_stats
    })