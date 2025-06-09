from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report dashboard
    path('', views.reports_dashboard, name='dashboard'),
    path('analytics_dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # Generate reports
    path('generate/', views.generate_report, name='generate'),
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('leave/', views.leave_report, name='leave_report'),
    path('employee/', views.employee_report, name='employee_report'),
    path('department/', views.department_report, name='department_report'),
    
    # Download reports
    path('download/<int:report_id>/', views.download_report, name='download'),
    path('download/<int:report_id>/', views.download_report, name='download'),
    path('delete/<int:report_id>/', views.delete_report, name='delete'),
    # API endpoints
    path('api/generate/', views.generate_report_api, name='generate_api'),
    path('api/list/', views.reports_list_api, name='list_api'),
    path('api/attendance-data/', views.attendance_data_api, name='attendance_data_api'),
]