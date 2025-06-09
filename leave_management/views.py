
from accounts.decorators import hr_required, admin_required, role_required, data_owner_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from .models import LeaveRequest, LeaveType, LeaveBalance
from accounts.models import User
import json
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def leave_balance(request):
    """View leave balances"""
    
    balances = LeaveBalance.objects.filter(
        user=request.user,
        year=timezone.now().year
    ).select_related('leave_type')
    
  
    existing_types = balances.values_list('leave_type_id', flat=True)
    all_leave_types = LeaveType.objects.filter(is_active=True)
    
    for leave_type in all_leave_types:
        if leave_type.id not in existing_types:
            LeaveBalance.objects.create(
                user=request.user,
                leave_type=leave_type,
                year=timezone.now().year,
                allocated_days=leave_type.max_days_per_year,
                used_days=0
            )
    

    balances = LeaveBalance.objects.filter(
        user=request.user,
        year=timezone.now().year
    ).select_related('leave_type')
    
    context = {
        'balances': balances,
        'page_title': 'Leave Balance',
        'current_year': timezone.now().year
    }
    return render(request, 'leave_management/balance.html', context)

@login_required
def leave_dashboard(request):
    """Leave management dashboard"""
    user = request.user
    
 
    if request.method == 'POST':
        try:
            leave_type = request.POST.get('leave_type') 
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            reason = request.POST.get('reason')
            
         
            if not all([leave_type, start_date, end_date, reason]):
                messages.error(request, 'All fields are required.')
                return redirect('leave_management:dashboard')
            

            valid_choices = [choice[0] for choice in LeaveRequest.LEAVE_CHOICES]
            if leave_type not in valid_choices:
                messages.error(request, 'Invalid leave type selected.')
                return redirect('leave_management:dashboard')
            
    
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid date format.')
                return redirect('leave_management:dashboard')
            
       
            if start_date > end_date:
                messages.error(request, 'Start date cannot be after end date.')
                return redirect('leave_management:dashboard')
            
            if start_date < timezone.now().date():
                messages.error(request, 'Start date cannot be in the past.')
                return redirect('leave_management:dashboard')
            
       
            total_days = (end_date - start_date).days + 1
            
           
            leave_request = LeaveRequest.objects.create(
                user=user,
                leave_type=leave_type,  
                start_date=start_date,
                end_date=end_date,
                total_days=total_days,
                reason=reason,
                status='pending'  
            )
            
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('leave_management:dashboard')
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('leave_management:dashboard')
    
  
    if user.is_admin_or_hr:
     
        my_requests = LeaveRequest.objects.select_related(
            'user', 'approved_by'
        ).order_by('-created_at')[:10]
        
        pending_requests = LeaveRequest.objects.filter(
            status='pending'
        ).select_related('user', 'approved_by').order_by('-created_at')
    else:
    
        my_requests = LeaveRequest.objects.filter(user=user).select_related('approved_by').order_by('-created_at')[:5]
        pending_requests = []
    
 
    leave_balances = LeaveBalance.objects.filter(
        user=user,
        year=timezone.now().year
    ).select_related('leave_type')
    

    existing_types = leave_balances.values_list('leave_type_id', flat=True)
    all_leave_types = LeaveType.objects.filter(is_active=True)
    
    for leave_type in all_leave_types:
        if leave_type.id not in existing_types:
            LeaveBalance.objects.create(
                user=request.user,
                leave_type=leave_type,
                year=timezone.now().year,
                allocated_days=leave_type.max_days_per_year,
                used_days=0
            )
    
    leave_balances = LeaveBalance.objects.filter(
        user=user,
        year=timezone.now().year
    ).select_related('leave_type')
    

    requests = LeaveRequest.objects.filter(
        user=request.user
    ).select_related('approved_by').order_by('-created_at')
    
   
    requests_data = []
    for req in requests:
        requests_data.append({
            'id': req.id,
            'leave_type': req.get_leave_type_display(),  
            'start_date': req.start_date.isoformat(),
            'end_date': req.end_date.isoformat(),
            'total_days': req.total_days,
            'status': req.status,
            'reason': req.reason,
            'created_at': req.created_at.isoformat(),
            'approved_by': str(req.approved_by) if req.approved_by else None,
            'approved_at': req.approved_at.isoformat() if req.approved_at else None,
        })
    
  
    leave_choices = LeaveRequest.LEAVE_CHOICES
    
    context = {
        'requests': requests,
        'requests_json': json.dumps(requests_data, cls=DjangoJSONEncoder),
        'my_requests': my_requests,
        'pending_requests': pending_requests,
        'leave_balances': leave_balances,
        'leave_choices': leave_choices,  
        'today': timezone.now().date(),
        'page_title': 'Leave Management'
    }
    return render(request, 'leave_management/dashboard.html', context)

@login_required
def create_leave_request(request):
    """Create a new leave request"""
    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')  
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')
        
        try:
          
            valid_choices = [choice[0] for choice in LeaveRequest.LEAVE_CHOICES]
            if leave_type not in valid_choices:
                messages.error(request, 'Invalid leave type selected.')
                return redirect('leave_management:create_request')
            
        
            leave_request = LeaveRequest.objects.create(
                user=request.user,
                leave_type=leave_type, 
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                reason=reason
            )
            
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('leave_management:my_requests')
            
        except Exception as e:
            messages.error(request, f'Error creating leave request: {str(e)}')
    
    leave_choices = LeaveRequest.LEAVE_CHOICES
    context = {
        'leave_choices': leave_choices,
        'page_title': 'Request Leave'
    }
    return render(request, 'leave_management/create_request.html', context)

@login_required
def my_leave_requests(request):
    """View user's leave requests"""
   
    requests = LeaveRequest.objects.filter(
        user=request.user
    ).select_related('approved_by').order_by('-created_at')
    

    requests_data = []
    for req in requests:
        requests_data.append({
            'id': req.id,
            'leave_type': req.get_leave_type_display(),
            'start_date': req.start_date.isoformat(),
            'end_date': req.end_date.isoformat(),
            'total_days': req.total_days,
            'status': req.status,
            'reason': req.reason,
            'created_at': req.created_at.isoformat(),
            'approved_by': str(req.approved_by) if req.approved_by else None,
            'approved_at': req.approved_at.isoformat() if req.approved_at else None,
        })
    
    context = {
        'requests': requests,
        'requests_json': json.dumps(requests_data, cls=DjangoJSONEncoder),
        'page_title': 'My Leave Requests'
    }
    return render(request, 'leave_management/my_requests.html', context)

@login_required
def leave_request_detail(request, request_id):
    """View leave request details"""
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    

    if leave_request.user != request.user and not request.user.is_admin_or_hr:
        messages.error(request, 'Access denied.')
        return redirect('leave_management:dashboard')
    
    context = {
        'leave_request': leave_request,
        'page_title': 'Leave Request Details'
    }
    return render(request, 'leave_management/request_detail.html', context)

@hr_required
def pending_requests(request):
    """View pending leave requests (Admin/HR only)"""
   
    requests = LeaveRequest.objects.filter(
        status='pending'
    ).select_related('user', 'approved_by').order_by('-created_at')
    
    context = {
        'requests': requests,
        'page_title': 'Pending Leave Requests'
    }
    return render(request, 'leave_management/pending_requests.html', context)

@hr_required
def approve_request(request, request_id):
    """Approve a leave request"""
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    
    if leave_request.status != 'pending':
        messages.warning(request, 'This request has already been processed.')
        return redirect('leave_management:pending_requests')
    

    leave_request.status = 'approved'
    leave_request.approved_by = request.user
    leave_request.approved_at = timezone.now()
    leave_request.save()
    
 
    try:
   
        leave_type_mapping = {
            'sick': 'Sick Leave',
            'vacation': 'Vacation',
           
        }
        
        leave_type_name = leave_type_mapping.get(leave_request.leave_type, leave_request.get_leave_type_display())
        leave_type_obj = LeaveType.objects.filter(name__icontains=leave_type_name).first()
        
        if leave_type_obj:
            leave_balance, created = LeaveBalance.objects.get_or_create(
                user=leave_request.user,
                leave_type=leave_type_obj,
                year=timezone.now().year,
                defaults={
                    'allocated_days': leave_type_obj.max_days_per_year,
                    'used_days': 0
                }
            )
            leave_balance.used_days += leave_request.total_days
            leave_balance.save()
    except Exception as e:
      
        print(f"Error updating leave balance: {e}")
    
    user_display_name = getattr(leave_request.user, 'full_name', str(leave_request.user))
    messages.success(request, f'Leave request for {user_display_name} has been approved.')
    return redirect('leave_management:pending_requests')

@hr_required
def reject_request(request, request_id):
    """Reject a leave request"""
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    
    if leave_request.status != 'pending':
        messages.warning(request, 'This request has already been processed.')
        return redirect('leave_management:pending_requests')
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        
        leave_request.status = 'rejected'
        leave_request.approved_by = request.user
        leave_request.approved_at = timezone.now()
        leave_request.rejection_reason = rejection_reason
        leave_request.save()
        
        user_display_name = getattr(leave_request.user, 'full_name', str(leave_request.user))
        messages.success(request, f'Leave request for {user_display_name} has been rejected.')
        return redirect('leave_management:pending_requests')
    
    context = {
        'leave_request': leave_request,
        'page_title': 'Reject Leave Request'
    }
    return render(request, 'leave_management/reject_request.html', context)


@hr_required
def all_requests(request):
    """View all leave requests (Admin/HR only)"""

    requests = LeaveRequest.objects.select_related(
        'user', 'approved_by'
    ).order_by('-created_at')
    

    status_filter = request.GET.get('status')
    department_filter = request.GET.get('department')
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    if department_filter:
        requests = requests.filter(user__department=department_filter)
    
   
    departments = User.objects.exclude(
        department__isnull=True
    ).exclude(
        department__exact=''
    ).values_list('department', flat=True).distinct().order_by('department')
    
    context = {
        'requests': requests,
        'departments': departments,
        'page_title': 'All Leave Requests',
        'current_filters': {
            'status': status_filter or '',
            'department': department_filter or '',
        }
    }
    return render(request, 'leave_management/all_requests.html', context)


@login_required
@csrf_exempt
def create_leave_api(request):
    """API endpoint to create leave request"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        leave_type = data['leave_type']  
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
      
        valid_choices = [choice[0] for choice in LeaveRequest.LEAVE_CHOICES]
        if leave_type not in valid_choices:
            return JsonResponse({'error': 'Invalid leave type'}, status=400)
        
        leave_request = LeaveRequest.objects.create(
            user=request.user,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=data['reason']
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Leave request created successfully',
            'request_id': leave_request.id,
            'total_days': leave_request.total_days
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

@login_required
def my_requests_api(request):
    """API endpoint for user's leave requests"""
    try:
        # NO select_related on leave_type for LeaveRequest!
        requests = LeaveRequest.objects.filter(
            user=request.user
        ).select_related('approved_by').order_by('-created_at')
        
        data = []
        for req in requests:
            try:
                # Get display name for CharField choices
                leave_type_name = req.get_leave_type_display()
                
                approved_by_name = None
                if req.approved_by:
                    approved_by_name = getattr(req.approved_by, 'full_name', str(req.approved_by))
                
                start_date = req.start_date.strftime('%Y-%m-%d') if req.start_date else None
                end_date = req.end_date.strftime('%Y-%m-%d') if req.end_date else None
                created_at = req.created_at.isoformat() if req.created_at else None
                approved_at = req.approved_at.isoformat() if req.approved_at else None
                
                data.append({
                    'id': req.id,
                    'leave_type': leave_type_name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_days': req.total_days or 0,
                    'reason': req.reason or '',
                    'status': req.status or 'pending',
                    'approved_by': approved_by_name,
                    'approved_at': approved_at,
                    'created_at': created_at
                })
            except Exception as item_error:
                print(f"Error processing leave request {req.id}: {item_error}")
                continue
        
        return JsonResponse({'requests': data})
        
    except Exception as e:
        print(f"Error in my_requests_api: {e}")
        return JsonResponse({
            'error': 'Failed to load leave requests',
            'requests': []
        }, status=500)

@hr_required
def pending_requests_api(request):
    """API endpoint for pending requests (Admin/HR only)"""
    
    requests = LeaveRequest.objects.filter(
        status='pending'
    ).select_related('user', 'approved_by').order_by('-created_at')
    
    data = []
    for req in requests:
        user_display_name = getattr(req.user, 'full_name', str(req.user))
        data.append({
            'id': req.id,
            'employee': user_display_name,
            'employee_id': getattr(req.user, 'employee_id', 'N/A'),
            'department': getattr(req.user, 'department', 'N/A'),
            'leave_type': req.get_leave_type_display(),
            'start_date': req.start_date.strftime('%Y-%m-%d'),
            'end_date': req.end_date.strftime('%Y-%m-%d'),
            'total_days': req.total_days,
            'reason': req.reason,
            'created_at': req.created_at.isoformat()
        })
    
    return JsonResponse({'requests': data})

@hr_required
@csrf_exempt
def approve_request_api(request, request_id):
    """API endpoint to approve leave request"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        leave_request = LeaveRequest.objects.get(id=request_id)
        
        if leave_request.status != 'pending':
            return JsonResponse({
                'error': 'Request already processed'
            }, status=400)
        
        # Approve request
        leave_request.status = 'approved'
        leave_request.approved_by = request.user
        leave_request.approved_at = timezone.now()
        leave_request.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Leave request approved successfully'
        })
        
    except LeaveRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@hr_required
@csrf_exempt
def reject_request_api(request, request_id):
    """API endpoint to reject leave request"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        leave_request = LeaveRequest.objects.get(id=request_id)
        
        if leave_request.status != 'pending':
            return JsonResponse({
                'error': 'Request already processed'
            }, status=400)
        
        # Reject request
        leave_request.status = 'rejected'
        leave_request.approved_by = request.user
        leave_request.approved_at = timezone.now()
        leave_request.rejection_reason = data.get('reason', '')
        leave_request.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Leave request rejected successfully'
        })
        
    except LeaveRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def approved_requests_api(request):
    """API endpoint for approved leave requests (for admin dashboard)"""
    try:
        if request.user.is_admin_or_hr:
            # NO select_related on leave_type for LeaveRequest!
            requests = LeaveRequest.objects.filter(
                status='approved'
            ).select_related('user', 'approved_by').order_by('-approved_at')[:20]
        else:
            requests = LeaveRequest.objects.filter(
                user=request.user,
                status='approved'
            ).select_related('approved_by').order_by('-approved_at')[:10]
        
        data = []
        for req in requests:
            try:
                leave_type_name = req.get_leave_type_display()
                
                approved_by_name = None
                if req.approved_by:
                    if hasattr(req.approved_by, 'full_name'):
                        approved_by_name = req.approved_by.full_name
                    elif hasattr(req.approved_by, 'get_full_name'):
                        approved_by_name = req.approved_by.get_full_name()
                    else:
                        approved_by_name = str(req.approved_by)
                
                employee_name = None
                department = None
                if request.user.is_admin_or_hr:
                    if hasattr(req.user, 'full_name'):
                        employee_name = req.user.full_name
                    elif hasattr(req.user, 'get_full_name'):
                        employee_name = req.user.get_full_name()
                    else:
                        employee_name = str(req.user)
                    department = getattr(req.user, 'department', 'N/A')
                
                data.append({
                    'id': req.id,
                    'employee_name': employee_name,
                    'department': department,
                    'leave_type': leave_type_name,
                    'start_date': req.start_date.strftime('%Y-%m-%d') if req.start_date else None,
                    'end_date': req.end_date.strftime('%Y-%m-%d') if req.end_date else None,
                    'total_days': req.total_days or 0,
                    'reason': req.reason or '',
                    'status': req.status or 'approved',
                    'approved_by': approved_by_name,
                    'approved_at': req.approved_at.isoformat() if req.approved_at else None,
                    'created_at': req.created_at.isoformat() if req.created_at else None
                })
            except Exception as item_error:
                print(f"Error processing approved request {req.id}: {item_error}")
                continue
        
        return JsonResponse({'requests': data})
        
    except Exception as e:
        print(f"Error in approved_requests_api: {e}")
        return JsonResponse({
            'error': 'Failed to load approved requests',
            'requests': []
        }, status=500)

@hr_required
def admin_stats_api(request):
    """API endpoint for admin dashboard statistics"""
    try:
        current_year = timezone.now().year
        
        # Get statistics for current year
        total_requests = LeaveRequest.objects.filter(
            created_at__year=current_year
        ).count()
        
        pending_count = LeaveRequest.objects.filter(
            status='pending'
        ).count()
        
        approved_count = LeaveRequest.objects.filter(
            status='approved',
            created_at__year=current_year
        ).count()
        
        rejected_count = LeaveRequest.objects.filter(
            status='rejected',
            created_at__year=current_year
        ).count()
        
        return JsonResponse({
            'total_requests': total_requests,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count
        })
        
    except Exception as e:
        print(f"Error in admin_stats_api: {e}")
        return JsonResponse({
            'total_requests': 0,
            'pending_count': 0,
            'approved_count': 0,
            'rejected_count': 0
        }, status=500)

@hr_required  
def filtered_requests_api(request):
    """API endpoint for filtered leave requests (admin only)"""
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        department_filter = request.GET.get('department', '')
        
        # Base queryset - NO select_related on leave_type for LeaveRequest!
        requests = LeaveRequest.objects.select_related('user', 'approved_by').all()
        
        # Apply filters
        if status_filter:
            requests = requests.filter(status=status_filter)
        
        if department_filter:
            requests = requests.filter(user__department=department_filter)
        
        # Order by most recent
        requests = requests.order_by('-created_at')[:50]  # Limit to 50 for performance
        
        data = []
        for req in requests:
            try:
                leave_type_name = req.get_leave_type_display()
                
                approved_by_name = None
                if req.approved_by:
                    if hasattr(req.approved_by, 'full_name'):
                        approved_by_name = req.approved_by.full_name
                    elif hasattr(req.approved_by, 'get_full_name'):
                        approved_by_name = req.approved_by.get_full_name()
                    else:
                        approved_by_name = str(req.approved_by)
                
                if hasattr(req.user, 'full_name'):
                    employee_name = req.user.full_name
                elif hasattr(req.user, 'get_full_name'):
                    employee_name = req.user.get_full_name()
                else:
                    employee_name = str(req.user)
                    
                department = getattr(req.user, 'department', 'N/A')
                
                data.append({
                    'id': req.id,
                    'employee_name': employee_name,
                    'department': department,
                    'leave_type': leave_type_name,
                    'start_date': req.start_date.strftime('%Y-%m-%d') if req.start_date else None,
                    'end_date': req.end_date.strftime('%Y-%m-%d') if req.end_date else None,
                    'total_days': req.total_days or 0,
                    'reason': req.reason or '',
                    'status': req.status,
                    'approved_by': approved_by_name,
                    'approved_at': req.approved_at.isoformat() if req.approved_at else None,
                    'created_at': req.created_at.isoformat() if req.created_at else None
                })
            except Exception as item_error:
                print(f"Error processing filtered request {req.id}: {item_error}")
                continue
        
        return JsonResponse({'requests': data})
        
    except Exception as e:
        print(f"Error in filtered_requests_api: {e}")
        return JsonResponse({
            'error': 'Failed to load filtered requests',
            'requests': []
        }, status=500)

@login_required
def leave_balances_api(request):
    """API endpoint for user's leave balances"""
    try:
        current_year = timezone.now().year
        
        # LeaveBalance.leave_type IS a ForeignKey, so select_related is OK
        balances = LeaveBalance.objects.filter(
            user=request.user,
            year=current_year
        ).select_related('leave_type')
        
        # Create balances for leave types that don't exist
        existing_types = balances.values_list('leave_type_id', flat=True)
        all_leave_types = LeaveType.objects.filter(is_active=True)
        
        for leave_type in all_leave_types:
            if leave_type.id not in existing_types:
                LeaveBalance.objects.create(
                    user=request.user,
                    leave_type=leave_type,
                    year=current_year,
                    allocated_days=leave_type.max_days_per_year,
                    used_days=0
                )
        
        # Refresh balances
        balances = LeaveBalance.objects.filter(
            user=request.user,
            year=current_year
        ).select_related('leave_type')
        
        data = []
        for balance in balances:
            try:
                leave_type_name = getattr(balance.leave_type, 'name', 'Unknown') if balance.leave_type else 'Unknown'
                
                data.append({
                    'leave_type': leave_type_name,
                    'total': balance.allocated_days or 0,
                    'used': balance.used_days or 0,
                    'remaining': max(0, (balance.allocated_days or 0) - (balance.used_days or 0))
                })
            except Exception as item_error:
                print(f"Error processing balance {balance.id}: {item_error}")
                continue
        
        return JsonResponse({'balances': data})
        
    except Exception as e:
        print(f"Error in leave_balances_api: {e}")
        return JsonResponse({
            'error': 'Failed to load leave balances',
            'balances': []
        }, status=500)

@hr_required
def pending_api(request):
    """API endpoint for pending requests (renamed for clarity)"""
    try:
        # NO select_related on leave_type for LeaveRequest!
        requests = LeaveRequest.objects.filter(
            status='pending'
        ).select_related('user', 'approved_by').order_by('-created_at')
        
        data = []
        for req in requests:
            try:
                leave_type_name = req.get_leave_type_display()
                
                if hasattr(req.user, 'full_name'):
                    employee_name = req.user.full_name
                elif hasattr(req.user, 'get_full_name'):
                    employee_name = req.user.get_full_name()
                else:
                    employee_name = str(req.user)
                    
                department = getattr(req.user, 'department', 'N/A')
                
                data.append({
                    'id': req.id,
                    'employee_name': employee_name,
                    'department': department,
                    'leave_type': leave_type_name,
                    'start_date': req.start_date.strftime('%Y-%m-%d') if req.start_date else None,
                    'end_date': req.end_date.strftime('%Y-%m-%d') if req.end_date else None,
                    'total_days': req.total_days or 0,
                    'reason': req.reason or '',
                    'created_at': req.created_at.isoformat() if req.created_at else None
                })
            except Exception as item_error:
                print(f"Error processing pending request {req.id}: {item_error}")
                continue
        
        return JsonResponse({'requests': data})
        
    except Exception as e:
        print(f"Error in pending_api: {e}")
        return JsonResponse({
            'error': 'Failed to load pending requests',
            'requests': []
        }, status=500)

# Add these aliases for backward compatibility
approve_api = approve_request_api
reject_api = reject_request_api