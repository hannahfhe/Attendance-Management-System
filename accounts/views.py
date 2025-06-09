
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum, Count
from datetime import date, timedelta
from django.utils import timezone
from .models import User
import json

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
def dashboard_view(request):
    """Main dashboard view with attendance data"""
    user = request.user
    today = date.today()
    
 
    today_record = None
    recent_records = []
    stats = {
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
            'present_days': present_count,
            'absent_days': absent_count,
            'late_days': late_count,
            'monthly_hours': float(total_hours)
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
        'today_record': today_record,
        'recent_records': recent_records,
        'stats': stats,
        'pending_leaves': pending_leaves,
        'page_title': 'Dashboard'
    }
    
    return render(request, 'accounts/dashboard.html', context)

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