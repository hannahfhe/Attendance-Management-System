
import os
import django
from django.db import transaction


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from accounts.models import User
from leave_management.models import LeaveType, LeaveBalance
from django.contrib.auth.hashers import make_password

def create_leave_types():
    """Create default leave types"""
    print("Creating leave types...")
    
    leave_types = [
        {
            'name': 'Annual Leave',
            'description': 'Yearly vacation leave',
            'max_days_per_year': 21,
            'requires_approval': True,
        },
        {
            'name': 'Sick Leave', 
            'description': 'Medical leave for illness',
            'max_days_per_year': 10,
            'requires_approval': False,
        },
        {
            'name': 'Personal Leave',
            'description': 'Personal matters leave',
            'max_days_per_year': 5,
            'requires_approval': True,
        },
        {
            'name': 'Emergency Leave',
            'description': 'Urgent/emergency situations',
            'max_days_per_year': 3,
            'requires_approval': True,
        },
        {
            'name': 'Maternity Leave',
            'description': 'Maternity leave for new mothers',
            'max_days_per_year': 90,
            'requires_approval': True,
        },
        {
            'name': 'Paternity Leave',
            'description': 'Paternity leave for new fathers', 
            'max_days_per_year': 14,
            'requires_approval': True,
        },
    ]
    
    created_count = 0
    for leave_data in leave_types:
        leave_type, created = LeaveType.objects.get_or_create(
            name=leave_data['name'],
            defaults=leave_data
        )
        if created:
            created_count += 1
            print(f"✓ Created leave type: {leave_type.name}")
        else:
            print(f"- Leave type already exists: {leave_type.name}")
    
    print(f"Total leave types created: {created_count}")
    return LeaveType.objects.all()

def create_demo_users():
    """Create demo users for testing"""
    print("\nCreating demo users...")
    
    demo_users = [
        {
            'username': 'admin.user',
            'email': 'admin@company.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'employee_id': 'ADM001',
            'department': 'IT',
            'role': 'admin',
            'password': 'admin123',
            'is_staff': True,
            'is_superuser': True,
        },
        {
            'username': 'jane.smith',
            'email': 'jane.smith@company.com', 
            'first_name': 'Jane',
            'last_name': 'Smith',
            'employee_id': 'HR001',
            'department': 'HR',
            'role': 'hr',
            'password': 'password123',
            'phone': '+1234567890',
        },
        {
            'username': 'john.doe',
            'email': 'john.doe@company.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'employee_id': 'EMP001',
            'department': 'IT',
            'role': 'employee',
            'password': 'password123',
            'phone': '+1234567891',
        },
        {
            'username': 'mike.johnson',
            'email': 'mike.johnson@company.com',
            'first_name': 'Mike', 
            'last_name': 'Johnson',
            'employee_id': 'FIN001',
            'department': 'Finance',
            'role': 'employee',
            'password': 'password123',
            'phone': '+1234567892',
        },
        {
            'username': 'sarah.wilson',
            'email': 'sarah.wilson@company.com',
            'first_name': 'Sarah',
            'last_name': 'Wilson',
            'employee_id': 'MKT001',
            'department': 'Marketing',
            'role': 'employee',
            'password': 'password123',
            'phone': '+1234567893',
        }
    ]
    
    created_count = 0
    created_users = []
    
    for user_data in demo_users:
        password = user_data.pop('password')
        
      
        if User.objects.filter(username=user_data['username']).exists():
            print(f"- User already exists: {user_data['username']}")
            user = User.objects.get(username=user_data['username'])
            created_users.append(user)
            continue
        
      
        user = User.objects.create(**user_data)
        user.set_password(password)
        user.save()
        
        created_count += 1
        created_users.append(user)
        print(f"✓ Created user: {user.username} ({user.full_name}) - Role: {user.role}")
    
    print(f"Total users created: {created_count}")
    return created_users

def create_leave_balances(users, leave_types):
    """Create leave balances for all users"""
    print("\nCreating leave balances...")
    
    created_count = 0
    current_year = 2025
    
    for user in users:
        for leave_type in leave_types:
            balance, created = LeaveBalance.objects.get_or_create(
                user=user,
                leave_type=leave_type,
                year=current_year,
                defaults={
                    'allocated_days': leave_type.max_days_per_year,
                    'used_days': 0,
                    'remaining_days': leave_type.max_days_per_year
                }
            )
            
            if created:
                created_count += 1
                print(f"✓ Created leave balance: {user.username} - {leave_type.name}")
    
    print(f"Total leave balances created: {created_count}")

@transaction.atomic
def main():
    """Run all data creation functions"""
    print("=" * 60)
    print("Creating Demo Data for Attendance Management System")
    print("=" * 60)
    
    try:
    
        leave_types = create_leave_types()
        
 
        users = create_demo_users()
        
   
        create_leave_balances(users, leave_types)
        
        print("\n" + "=" * 60)
        print("✅ Demo data creation completed successfully!")
        print("=" * 60)
        print("\n🎮 Demo Login Credentials:")
        print("-" * 30)
        print("👑 Admin User:")
        print("   Username: admin.user")
        print("   Password: admin123")
        print("   Role: System Administrator")
        print()
        print("👔 HR Manager:")
        print("   Username: jane.smith")
        print("   Password: password123")
        print("   Role: HR Manager")
        print()
        print("👨‍💻 Employees:")
        print("   Username: joshua.doe")
        print("   Password: password123")
        print("   Role: Employee (IT Department)")
        print()
        print("   Username: mike.johnson")
        print("   Password: password123")
        print("   Role: Employee (Finance Department)")
        print()
        print("   Username: sarah.wilson")
        print("   Password: password123")
        print("   Role: Employee (Marketing Department)")
        print()
        print("🌐 Access URLs:")
        print("   Login: http://127.0.0.1:8000/")
        print("   Admin: http://127.0.0.1:8000/admin/")
        print()
        print("📝 Next Steps:")
        print("1. Run: python manage.py runserver")
        print("2. Visit: http://127.0.0.1:8000/")
        print("3. Login with any of the demo accounts above")
        print("4. Test the attendance and leave management features")
        
    except Exception as e:
        print(f"\n❌ Error creating demo data: {str(e)}")
        print("Please check your database connection and model configurations.")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()