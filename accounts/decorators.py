# ===============================================
# accounts/decorators.py (CREATE THIS NEW FILE)
# ===============================================

from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import User
from attendance.models import AttendanceRecord

def role_required(allowed_roles):
    """
    Decorator that requires user to have one of the specified roles.
    Usage: @role_required(['hr', 'admin'])
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'role'):
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'error': 'User role not defined'}, status=403)
                messages.error(request, 'Access denied: User role not defined')
                return redirect('accounts:dashboard')
            
            if request.user.role not in allowed_roles:
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'error': 'Access denied'}, status=403)
                messages.error(request, 'Access denied: Insufficient permissions')
                return redirect('accounts:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def hr_required(view_func):
    """
    Decorator that requires HR or Admin role.
    Usage: @hr_required
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'role'):
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'User role not defined'}, status=403)
            messages.error(request, 'Access denied: User role not defined')
            return redirect('accounts:dashboard')
        
        if request.user.role not in ['hr', 'admin']:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'HR access required'}, status=403)
            messages.error(request, 'Access denied: HR privileges required')
            return redirect('accounts:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    """
    Decorator that requires Admin role only.
    Usage: @admin_required
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'role'):
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'User role not defined'}, status=403)
            messages.error(request, 'Access denied: User role not defined')
            return redirect('accounts:dashboard')
        
        if request.user.role != 'admin':
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'Admin access required'}, status=403)
            messages.error(request, 'Access denied: Administrator privileges required')
            return redirect('accounts:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def manager_required(view_func):
    """
    Decorator that requires Manager, HR, or Admin role.
    Usage: @manager_required
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'role'):
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'User role not defined'}, status=403)
            messages.error(request, 'Access denied: User role not defined')
            return redirect('accounts:dashboard')
        
        if request.user.role not in ['manager', 'hr', 'admin']:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'Manager access required'}, status=403)
            messages.error(request, 'Access denied: Management privileges required')
            return redirect('accounts:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def employee_only(view_func):
    """
    Decorator that allows only regular employees (blocks admin/hr from employee-only views).
    Usage: @employee_only
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'role'):
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'User role not defined'}, status=403)
            messages.error(request, 'Access denied: User role not defined')
            return redirect('accounts:dashboard')
        
        if request.user.role != 'employee':
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'Employee-only access'}, status=403)
            messages.error(request, 'This feature is for employees only')
            return redirect('accounts:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def data_owner_required(view_func):
    """
    Decorator that checks if user can access specific user data.
    Allows: 
    - User accessing their own data
    - HR/Admin accessing any user data
    - Managers accessing their team data (if manager field is set)
    
    Usage: @data_owner_required
    Note: The view must accept 'user_id' parameter
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        from accounts.models import User
        
        # Get the target user ID from URL parameters
        target_user_id = kwargs.get('user_id')
        if not target_user_id:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'User ID required'}, status=400)
            messages.error(request, 'User ID required')
            return redirect('accounts:dashboard')
        
        # Admin and HR can access anyone's data
        if request.user.role in ['admin', 'hr']:
            return view_func(request, *args, **kwargs)
        
        # Users can access their own data
        if request.user.id == target_user_id:
            return view_func(request, *args, **kwargs)
        
        # Managers can access their subordinates' data
        if request.user.role == 'manager':
            try:
                target_user = User.objects.get(id=target_user_id)
                if target_user.manager == request.user:
                    return view_func(request, *args, **kwargs)
            except User.DoesNotExist:
                pass
        
        # Access denied
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'error': 'Access denied to user data'}, status=403)
        messages.error(request, 'Access denied: You can only access your own data')
        return redirect('accounts:dashboard')
    
    return wrapper


# ===============================================
# Example Usage in Views
# ===============================================

# UPDATE YOUR EXISTING VIEW FILES WITH THESE IMPORTS AND DECORATORS:

# At the top of each view file, add:
from accounts.decorators import hr_required, admin_required, role_required, data_owner_required

# ===============================================
# leave_management/views.py - UPDATE EXISTING FUNCTIONS
# ===============================================

# Add these imports at the top
from accounts.decorators import hr_required, admin_required, role_required

# Update existing functions:
@hr_required
def pending_requests(request):
    """View pending leave requests (Admin/HR only)"""
    # ... existing code ...

@hr_required
def approve_request(request, request_id):
    """Approve a leave request"""
    # ... existing code ...

@hr_required  
def reject_request(request, request_id):
    """Reject a leave request"""
    # ... existing code ...

@hr_required
def approve_request_api(request, request_id):
    """API endpoint to approve leave request"""
    # ... existing code ...

@hr_required
def reject_request_api(request, request_id):
    """API endpoint to reject leave request"""
    # ... existing code ...


# ===============================================
# attendance/views.py - UPDATE EXISTING FUNCTIONS  
# ===============================================

# Add these imports at the top
from accounts.decorators import hr_required, admin_required, data_owner_required

# Update existing functions:
@admin_required
def all_attendance_records(request):
    """Admin view for all attendance records"""
    # Remove the manual role check since decorator handles it
    records = AttendanceRecord.objects.all().order_by('-date', 'user__first_name')
    # ... rest of existing code ...

@data_owner_required
def employee_attendance(request, user_id):
    """Admin view for specific employee attendance"""
    # Remove manual role check since decorator handles it
    employee = get_object_or_404(User, id=user_id)
    # ... rest of existing code ...


# ===============================================
# reports/views.py - UPDATE EXISTING FUNCTIONS
# ===============================================

# Add these imports at the top
from accounts.decorators import hr_required, admin_required

# Update existing functions:
@hr_required
def reports_dashboard(request):
    """Reports dashboard view"""
    # Remove manual role check since decorator handles it
    # ... rest of existing code ...

@hr_required
def generate_report(request):
    """Generate report form"""
    # Remove manual role check since decorator handles it
    # ... rest of existing code ...

@hr_required
def attendance_report(request):
    """Attendance report view"""
    # Remove manual role check since decorator handles it
    # ... rest of existing code ...

@hr_required
def leave_report(request):
    """Leave report view"""
    # Remove manual role check since decorator handles it
    # ... rest of existing code ...

@hr_required
def employee_report(request):
    """Employee-wise report"""
    # Remove manual role check since decorator handles it
    # ... rest of existing code ...

@hr_required
def department_report(request):
    """Department-wise report"""
    # Remove manual role check since decorator handles it
    # ... rest of existing code ...

@hr_required
def download_report(request, report_id):
    """Download generated report"""
    # Remove manual role check since decorator handles it
    # ... rest of existing code ...

# All API endpoints in reports should also be decorated:
@hr_required
def generate_report_api(request):
    """API endpoint to generate reports"""
    # ... existing code ...

@hr_required
def reports_list_api(request):
    """API endpoint to get list of reports"""
    # ... existing code ...

@hr_required
def attendance_data_api(request):
    """API endpoint for attendance data (for charts/graphs)"""
    # ... existing code ...


# ===============================================
# Advanced Usage Examples
# ===============================================

# Multiple roles allowed:
@role_required(['hr', 'admin', 'manager'])
def team_overview(request):
    """View accessible to HR, Admin, and Managers"""
    pass

# Chain decorators for complex permissions:
@admin_required
@login_required
def system_settings(request):
    """Only admins can access system settings"""
    pass

# Custom permission logic:
@role_required(['hr', 'admin'])
def sensitive_employee_data(request, employee_id):
    """HR and Admin can view sensitive employee data"""
    # Additional custom logic can go here
    pass