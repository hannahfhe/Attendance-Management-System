
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Main views
    path('', views.attendance_dashboard, name='dashboard'),
    path('records/', views.attendance_records, name='records'),
    
    # Check in/out actions
    path('checkin/', views.check_in_view, name='checkin'),
    path('checkout/', views.check_out_view, name='checkout'),
    
    # Admin actions
    path('admin/checkout/<int:record_id>/', views.admin_checkout, name='admin_checkout'),
    path('employee/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('export/', views.export_data, name='export_data'),
]