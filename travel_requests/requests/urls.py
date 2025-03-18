from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    
    # Admin Requests Endpoints  
    path('api/admin/requests/',views.listing_requests_admin), 
    path('api/admin/requests/<int:request_id>/',views.view_request_employee),  
    path('api/admin/requests/<int:request_id>/close/',views.close_request_admin),

    # Admin Employees Endpoints
    path('api/admin/employees/',views.listing_employees_admin),  
    path('api/admin/employees/<int:employee_id>/',views.view_employee_admin),
    path('api/admin/employees/new/',views.new_employee), 
    
    # Manager Requests Endpoints
    path('api/manager/requests/',views.listing_requests_manager),   
    path('api/manager/requests/<int:request_id>/',views.view_request_employee),
    path('api/manager/requests/<int:request_id>/action/',views.action_request_manager),

    # Employee Requests Endpoints
    path('api/employee/requests/',views.listing_requests_employee),  
    path('api/employee/requests/new/',views.emp_request_form), 
    path('employee/me/',views.get_logged_in_employee_details), 
    path('api/employee/requests/<int:request_id>/view/',views.view_request_employee),
    path('api/employee/requests/<int:request_id>/edit/',views.edit_request_employee), 
    path('api/employee/requests/<int:request_id>/action/',views.action_request_employee),

    # Authentication Endpoints
    path('api/auth/employee/login/',views.employee_login), 
    path('api/auth/manager/login/',views.manager_login),  
    path('api/auth/admin/login/',views.admin_login), 
    path('api/auth/admin/create/',views.create_admin),  
]
