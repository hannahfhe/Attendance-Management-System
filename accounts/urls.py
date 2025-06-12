# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Profile Management
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    
    # Employee Management (CRUD)
    path('employees/', views.employee_list_view, name='employee_list'),
    path('employee/<int:employee_id>/', views.employee_detail_view, name='employee_detail'),
    path('employee/create/', views.employee_create_view, name='employee_create'),
    path('employee/<int:employee_id>/edit/', views.employee_edit_view, name='employee_edit'),
    path('employee/<int:employee_id>/delete/', views.employee_delete_view, name='employee_delete'),
    path('employee/<int:employee_id>/toggle-status/', views.employee_toggle_status_view, name='employee_toggle_status'),
    
    # API endpoints
    path('api/user-info/', views.user_info_api, name='user_info_api'),
]