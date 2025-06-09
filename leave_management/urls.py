

from django.urls import path
from . import views

app_name = 'leave_management'

urlpatterns = [
    # Main pages
    path('', views.leave_dashboard, name='dashboard'),
    path('create/', views.create_leave_request, name='create_request'),
    path('my-requests/', views.my_leave_requests, name='my_requests'),
    path('request/<int:request_id>/', views.leave_request_detail, name='request_detail'),
    path('balance/', views.leave_balance, name='balance'),
    
    # Admin/HR pages
    path('pending/', views.pending_requests, name='pending_requests'),
    path('all-requests/', views.all_requests, name='all_requests'),
    path('approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject/<int:request_id>/', views.reject_request, name='reject_request'),
    
    # API endpoints for regular users
    path('api/create/', views.create_leave_api, name='create_api'),
    path('api/my-requests/', views.my_requests_api, name='my_requests_api'),
    path('api/balances/', views.leave_balances_api, name='balances_api'),
    
    # API endpoints for admin dashboard
    path('api/approved-requests/', views.approved_requests_api, name='approved_requests_api'),
    path('api/admin/stats/', views.admin_stats_api, name='admin_stats_api'),
    path('api/admin/pending/', views.pending_api, name='pending_api'),
    path('api/admin/filtered/', views.filtered_requests_api, name='filtered_requests_api'),
    
    # API endpoints for approval actions
    path('api/approve/<int:request_id>/', views.approve_request_api, name='approve_api'),
    path('api/reject/<int:request_id>/', views.reject_request_api, name='reject_api'),
]