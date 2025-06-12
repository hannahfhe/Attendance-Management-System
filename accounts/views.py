
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum, Count, Q
from datetime import date, timedelta
from django.utils import timezone
from .models import User
import json

@login_required
def dashboard_view(request):
    from leave_management.models import LeaveRequest
    """Main dashboard view with attendance data"""
    user = request.user
    today = date.today()
    
 
    today_record = None
    recent_records = []
    stats = {
        'total_employees': User.objects.all().count(),
        'present_days': 0,
        'absent_days': 0,
        'late_days': 0,
        'monthly_hours': 0
    }
    pending_leaves = 0
    
  
    try:
        from attendance.models import AttendanceRecord
        
        #
        today_record = AttendanceRecord.objects.filter(
            user=user,
            date=today
        ).first()
        
   
        recent_records = AttendanceRecord.objects.filter(
            user=user
        ).order_by('-date')[:5]
        
      
        current_month = today.month
        current_year = today.year
        
        monthly_records = AttendanceRecord.objects.filter(
            user=user,
            date__month=current_month,
            date__year=current_year
        )
        
        
        present_count = monthly_records.filter(
            status__in=['present', 'late']
        ).count()
        
        absent_count = monthly_records.filter(
            status='absent'
        ).count()
        
        late_count = monthly_records.filter(
            is_late=True
        ).count()
        
        total_hours = monthly_records.aggregate(
            total=Sum('total_hours')
        )['total'] or 0
        
        stats = {
            'total_employees': User.objects.all().count(),
            'present_days': present_count,
            'absent_days': absent_count,
            'late_days': late_count,
            'monthly_hours': float(total_hours),
           
          
           
        }
        
    except ImportError:
       
        pass
    except Exception as e:
 
        print(f"Error loading attendance data: {e}")
    
 
    try:
        from leave_management.models import LeaveRequest
        pending_leaves = LeaveRequest.objects.filter(
            user=user,
            status='pending'
        ).count()
    except ImportError:
     
        pass
    except Exception as e:
        
        print(f"Error loading leave data: {e}")
    
    context = {
        'user': user,
        'today_record': AttendanceRecord.objects.filter(Q(check_in_time__isnull=False), Q(date=date.today())).count(),
        'recent_records': recent_records,
        'stats': stats,
        'pending_leaves': LeaveRequest.objects.filter(status='pending').count(),
        'page_title': 'Dashboard'
    }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def employee_list_view(request):
    """Employee list view with search and filtering - Only for HR/Admin"""
    
    # Check if user has permission to view employee list
    if not request.user.is_admin_or_hr:
        messages.error(request, 'You do not have permission to access the employee list.')
        return redirect('accounts:dashboard')
    
    # Get all employees
    employees = User.objects.all().order_by('first_name', 'last_name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Department filter
    department_filter = request.GET.get('department', '')
    if department_filter:
        employees = employees.filter(department=department_filter)
    
    # Role filter  
    role_filter = request.GET.get('role', '')
    if role_filter:
        employees = employees.filter(role=role_filter)
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(employees, 20)  # Show 20 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter choices for the template
    departments = User.DEPARTMENT_CHOICES
    roles = User.ROLE_CHOICES
    
    # Statistics
    total_employees = User.objects.count()
    active_employees = User.objects.filter(is_active=True).count()
    inactive_employees = total_employees - active_employees
    
    # Get department counts
    department_stats = {}
    for dept_code, dept_name in departments:
        count = User.objects.filter(department=dept_code).count()
        if count > 0:
            department_stats[dept_name] = count
    
    context = {
        'employees': page_obj,
        'search_query': search_query,
        'department_filter': department_filter,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'departments': departments,
        'roles': roles,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'department_stats': department_stats,
        'page_title': 'Employee List'
    }
    
    return render(request, 'accounts/employee_list.html', context)

@login_required
def employee_detail_view(request, employee_id):
    """Employee detail view - Only for HR/Admin"""
    
    if not request.user.is_admin_or_hr:
        messages.error(request, 'You do not have permission to view employee details.')
        return redirect('accounts:dashboard')
    
    employee = get_object_or_404(User, id=employee_id)
    
    # Get recent attendance data if available
    recent_attendance = []
    try:
        from attendance.models import AttendanceRecord
        recent_attendance = AttendanceRecord.objects.filter(
            user=employee
        ).order_by('-date')[:10]
    except ImportError:
        pass
    
    # Get recent leave requests if available
    recent_leaves = []
    try:
        from leave_management.models import LeaveRequest
        recent_leaves = LeaveRequest.objects.filter(
            user=employee
        ).order_by('-created_at')[:5]
    except ImportError:
        pass
    
    context = {
        'employee': employee,
        'recent_attendance': recent_attendance,
        'recent_leaves': recent_leaves,
        'page_title': f'Employee Details - {employee.full_name}'
    }
    
    return render(request, 'accounts/employee_detail.html', context)

@login_required
def employee_create_view(request):
    """Create new employee - Only for HR/Admin"""
    
    if not request.user.is_admin_or_hr:
        messages.error(request, 'You do not have permission to create employees.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
       
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        employee_id = request.POST.get('employee_id')
        department = request.POST.get('department')
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        errors = []
        
        if not all([username, email, first_name, last_name, password]):
            errors.append('All required fields must be filled.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        
        if User.objects.filter(email=email).exists():
            errors.append('Email already exists.')
        
        if employee_id and User.objects.filter(employee_id=employee_id).exists():
            errors.append('Employee ID already exists.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    employee_id=employee_id or None,
                    department=department or '',
                    role=role or 'employee',
                    phone=phone or '',
                    password=password,
                    is_active=is_active
                )
                messages.success(request, f'Employee {user.full_name} created successfully!')
                return redirect('accounts:employee_detail', employee_id=user.id)
            except Exception as e:
                messages.error(request, f'Error creating employee: {str(e)}')
    
    context = {
        'departments': User.DEPARTMENT_CHOICES,
        'roles': User.ROLE_CHOICES,
        'page_title': 'Create New Employee'
    }
    
    return render(request, 'accounts/employee_create.html', context)

@login_required
def employee_edit_view(request, employee_id):
    """Edit employee - Only for HR/Admin"""
    
    if not request.user.is_admin_or_hr:
        messages.error(request, 'You do not have permission to edit employees.')
        return redirect('accounts:dashboard')
    
    employee = get_object_or_404(User, id=employee_id)
    
    if request.method == 'POST':
       
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        employee_id_field = request.POST.get('employee_id')
        department = request.POST.get('department')
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        is_active = request.POST.get('is_active') == 'on'
        
       
        errors = []
        
        if not all([username, email, first_name, last_name]):
            errors.append('All required fields must be filled.')
        
      
        if User.objects.filter(username=username).exclude(id=employee.id).exists():
            errors.append('Username already exists.')
        
        if User.objects.filter(email=email).exclude(id=employee.id).exists():
            errors.append('Email already exists.')
        
        if employee_id_field and User.objects.filter(employee_id=employee_id_field).exclude(id=employee.id).exists():
            errors.append('Employee ID already exists.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                employee.username = username
                employee.email = email
                employee.first_name = first_name
                employee.last_name = last_name
                employee.employee_id = employee_id_field or None
                employee.department = department or ''
                employee.role = role or 'employee'
                employee.phone = phone or ''
                employee.is_active = is_active
                employee.save()
                
                messages.success(request, f'Employee {employee.full_name} updated successfully!')
                return redirect('accounts:employee_detail', employee_id=employee.id)
            except Exception as e:
                messages.error(request, f'Error updating employee: {str(e)}')
    
    context = {
        'employee': employee,
        'departments': User.DEPARTMENT_CHOICES,
        'roles': User.ROLE_CHOICES,
        'page_title': f'Edit Employee - {employee.full_name}'
    }
    
    return render(request, 'accounts/employee_edit.html', context)

@login_required
def employee_delete_view(request, employee_id):
    """Delete employee - Only for HR/Admin"""
    
    if not request.user.is_admin_or_hr:
        messages.error(request, 'You do not have permission to delete employees.')
        return redirect('accounts:dashboard')
    
    employee = get_object_or_404(User, id=employee_id)
    
    # Prevent deleting self
    if employee == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:employee_list')
    
    if request.method == 'POST':
        employee_name = employee.full_name
        employee.delete()
        messages.success(request, f'Employee {employee_name} has been deleted successfully.')
        return redirect('accounts:employee_list')
    
    context = {
        'employee': employee,
        'page_title': f'Delete Employee - {employee.full_name}'
    }
    
    return render(request, 'accounts/employee_delete.html', context)

@login_required
def employee_toggle_status_view(request, employee_id):
    """Toggle employee status - Only for HR/Admin"""
    
    if not request.user.is_admin_or_hr:
        messages.error(request, 'You do not have permission to change employee status.')
        return redirect('accounts:dashboard')
    
    employee = get_object_or_404(User, id=employee_id)
    
    # Prevent deactivating self
    if employee == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('accounts:employee_list')
    
    if request.method == 'POST':
        employee.is_active = not employee.is_active
        employee.save()
        
        status_text = 'activated' if employee.is_active else 'deactivated'
        messages.success(request, f'Employee {employee.full_name} has been {status_text}.')
    
    return redirect('accounts:employee_list')
def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        employee_id = request.POST.get('employee_id')
        department = request.POST.get('department')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
      
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(employee_id=employee_id).exists():
            messages.error(request, 'Employee ID already exists.')
            return render(request, 'accounts/register.html')
        

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                employee_id=employee_id,
                department=department,
                password=password
            )
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('accounts:login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'accounts/register.html')


@login_required
def profile_view(request):
    """User profile view"""
    context = {
        'user': request.user,
        'page_title': 'Profile'
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile_view(request):
    """Edit user profile"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/edit_profile.html', {'user': request.user})

def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')

@login_required
@csrf_exempt
def user_info_api(request):
    """API endpoint for user information"""
    user = request.user
    data = {
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'email': user.email,
        'employee_id': user.employee_id,
        'department': user.department,
        'role': user.role,
        'is_admin': user.is_admin_or_hr,
    }
    return JsonResponse(data)