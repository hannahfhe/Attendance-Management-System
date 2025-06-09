
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from leave_management.models import LeaveRequest, LeaveType, LeaveBalance
from accounts.models import User

def fix_leave_data():
    """Fix corrupted leave data"""
    print("=== FIXING LEAVE DATA ===")
    
    # 1. Check and fix leave requests with invalid leave_type
    print("\n1. Checking leave requests...")
    
    broken_requests = []
    for req in LeaveRequest.objects.all():
        try:
            # Try to access the leave_type name
            _ = req.leave_type.name
            print(f"   ✓ Request {req.id}: {req.leave_type.name}")
        except AttributeError:
            print(f"   ❌ Request {req.id}: Invalid leave_type (is string: {type(req.leave_type)})")
            broken_requests.append(req)
        except Exception as e:
            print(f"   ❌ Request {req.id}: Error accessing leave_type: {e}")
            broken_requests.append(req)
    
    # 2. Fix broken requests
    if broken_requests:
        print(f"\n2. Found {len(broken_requests)} broken requests. Fixing...")
        
        # Get first available leave type
        default_leave_type = LeaveType.objects.first()
        if not default_leave_type:
            print("   ❌ No leave types available! Creating default...")
            default_leave_type = LeaveType.objects.create(
                name='Annual Leave',
                description='Default leave type',
                max_days_per_year=21
            )
        
        for req in broken_requests:
            try:
                req.leave_type = default_leave_type
                req.save()
                print(f"   ✓ Fixed request {req.id}")
            except Exception as e:
                print(f"   ❌ Failed to fix request {req.id}: {e}")
    else:
        print("\n2. No broken requests found!")
    
    # 3. Check leave types
    print("\n3. Checking leave types...")
    leave_types = LeaveType.objects.all()
    if leave_types.exists():
        for lt in leave_types:
            print(f"   ✓ {lt.name} (ID: {lt.id})")
    else:
        print("   ❌ No leave types found! Creating default types...")
        create_default_leave_types()
    
    # 4. Verify all requests are working now
    print("\n4. Final verification...")
    try:
        for req in LeaveRequest.objects.all():
            _ = req.leave_type.name  # This should not crash now
            print(f"   ✓ Request {req.id}: {req.leave_type.name} - {req.status}")
        print("\n✅ All leave requests are now working!")
    except Exception as e:
        print(f"\n❌ Still have issues: {e}")

def create_default_leave_types():
    """Create default leave types if none exist"""
    default_types = [
        {'name': 'Annual Leave', 'max_days_per_year': 21},
        {'name': 'Sick Leave', 'max_days_per_year': 10},
        {'name': 'Personal Leave', 'max_days_per_year': 5},
        {'name': 'Emergency Leave', 'max_days_per_year': 3},
    ]
    
    for type_data in default_types:
        leave_type, created = LeaveType.objects.get_or_create(
            name=type_data['name'],
            defaults={
                'description': f"Default {type_data['name']}",
                'max_days_per_year': type_data['max_days_per_year'],
                'requires_approval': True,
                'is_active': True
            }
        )
        if created:
            print(f"   ✓ Created leave type: {leave_type.name}")

if __name__ == '__main__':
    fix_leave_data()
