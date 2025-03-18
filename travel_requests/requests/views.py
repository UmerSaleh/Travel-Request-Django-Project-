from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth.forms import UserCreationForm

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from .models import Admin, Request, Employee
from .serializers import TravelSerializer, EmployeeSerializer, AdminSerializer, UserSerializer
from .permissions import IsAdmin, IsManager, IsEmployee

from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)




#--------------------------------------------------------------Admin---------------------------------------------------------------#
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def listing_requests_admin(request):
    """
    View for listing requests for an admin.

    This endpoint allows the admin to filter and sort the list of requests.

    The response will be a list of requests matching the filters, sorted according to the provided sorting option.

    Permissions:
    - Only authenticated users with admin privileges can access this view.

    Parameters:
    - GET request with query parameters:
        - `status`: Optional; filter by request status.
        - `start_date`: Optional; filter by the start date of requests.
        - `end_date`: Optional; filter by the end date of requests.
        - `search_name`: Optional; filter by the employee's first or last name.
        - `sort_by`: Optional; sort by a specified field (e.g., date_of_request).
    """
    if request.method == "GET":
        try:
            # Check if the logged-in user is an Admin
            admin = Admin.objects.get(user=request.user)
            logger.info("Admin authentication successful ")
        except Admin.DoesNotExist:
            logger.warning("Admin does not exist")
            raise PermissionDenied("Admin does not exist")

        # Extract query parameters
        status_filter = request.query_params.get('status')
        sort_option = request.query_params.get('sort_by')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        search_name = request.query_params.get('search_name')

        # Query to get requests with related employee data (optimized with select_related)
        data = Request.objects.select_related('employee')

        if status_filter:
            data = data.filter(status_of_request=status_filter)

        if start_date and end_date:
            data = data.filter(date_of_request__range=[start_date, end_date])
        elif start_date:
            data = data.filter(date_of_request__gte=start_date)  # Greater than or equal to start_date
        elif end_date:
            data = data.filter(date_of_request__lte=end_date)  # Less than or equal to end_date # Date range filtering

        if search_name:
            data = data.filter(
                Q(employee__user__first_name__icontains=search_name) |
                Q(employee__user__last_name__icontains=search_name)
            ) # to filter by first_name from the User model, you must refer to the related User model through the user field in the Employee model.
        

        # Validate the sort option
        valid_sort_options = ['date_of_request', 'from_date']
        if sort_option:
            descending = sort_option.startswith('-')
            clean_sort_option = sort_option.lstrip('-') 

            if clean_sort_option in valid_sort_options:
                data = data.order_by(f"-{clean_sort_option}" if descending else clean_sort_option)

        # If no data matches the filter criteria, return an empty list message
        if not data.exists():
            return Response({'message': "No requests found"}, status=HTTP_404_NOT_FOUND)

        serialized = TravelSerializer(data, many=True)

        return Response(serialized.data, status=HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_request_employee(request,request_id):  
    """
    View for retrieving details of a specific request made by an employee.

    This endpoint allows an authenticated employee to view the details of a specific request using its ID.

    Permissions:
    - Only authenticated users can access this view.

    Parameters:
    - GET request with a path parameter `request_id` (the ID of the request to be viewed).
    """
    if request.method == "GET":
        try:
            selected_request = Request.objects.get(pk=request_id)
            logger.info("Request found: %s", request_id)
        except Request.DoesNotExist:
            logger.warning("Request not found: %s", request_id)
            return Response({"error": "Request not found"}, status=HTTP_404_NOT_FOUND)

        serialized = TravelSerializer(selected_request) 
        return Response(serialized.data, status=HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def close_request_admin(request,request_id):
    """
    Endpoint for closing a request by an admin.

    This endpoint allows an authenticated admin to close a request that has been approved. 
    The admin provides an action and an optional note to close the request.

    Permissions:
    - Only authenticated users with admin permissions can access this view.

    Parameters:
    - POST request with `request_id` (the ID of the request to be updated) and JSON body containing:
      - `action`: The action to be performed (should be "close").
      - `note`: Optional note from the admin.
    """
    if request.method == "POST":
        try:
            selected_request = Request.objects.get(pk=request_id)
            logger.info("Request found: %s", request_id)
        except Request.DoesNotExist:
            logger.warning("Request not found: %s", request_id)
            return Response({"error": "Request not found"}, status=HTTP_404_NOT_FOUND)

        if selected_request.status_of_request == "approved":
            action  = request.data.get('action')
            note = request.data.get('note')

            if not action:
                return Response({"message":"No action provided"}, status = HTTP_404_NOT_FOUND)

            if action == "close":
                selected_status = "closed"
            else:
                return Response({"error": "Invalid action"}, status=HTTP_400_BAD_REQUEST)
            
            
            serialized = TravelSerializer(selected_request, data={"status_of_request": selected_status, "message_from_admin": note}, partial=True)
            
            subject = 'Request submitted: Closed after Approval'
            message = f'Note:{note} \n Your request for travel has been closed. Thanks & Regards. - Admin'
            from_email = 'umersaleh30570@gmail.com'  
            recipient_list = [selected_request.employee.user.email]  

            if serialized.is_valid():
                serialized.save()
                send_mail(subject, message, from_email, recipient_list)
            else:
                return Response(serialized.errors,status = HTTP_400_BAD_REQUEST)
        
            return Response({"message":"Request status updated","action":action},status = HTTP_200_OK)
        else:
            logger.error("Request not approved yet")
            return Response({"error":"Request not approved yet!"},status = HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def listing_employees_admin(request):
    """
    Endpoint to list all employees for admins.

    This endpoint allows an authenticated admin to retrieve a list of all employees.
    Optionally, it supports searching by employee first or last name using the `search_name` query parameter.

    Permissions:
    - Only authenticated users with admin permissions can access this view.

    Parameters:
    - GET request with an optional query parameter:
        - `search_name`: String to search employee by first or last name.
    """

    if request.method == "GET":
        logger.info("Received request to list employees")

        search_name = request.query_params.get('search_name')

        data = Employee.objects.all()

        if search_name:  
            data = data.filter(
                Q(user__first_name__icontains=search_name) | Q(user__last_name__icontains=search_name)
            )
        #Q objects allow you to combine multiple query conditions with logical operators
        #Since you are using the Employee model, which has a user relationship (one-to-one) with the User model

        serialized = EmployeeSerializer(data, many=True)

        return Response(serialized.data,status = HTTP_200_OK)


@api_view(["GET","PATCH","DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def view_employee_admin(request,employee_id):  
    """
    Endpoint to view, update, or delete an employee for admins.

    This endpoint allows an admin to perform the following actions on an employee:
    - GET: View the details of a specific employee.
    - PATCH: Update specific employee or user details.
    - DELETE: Remove an employee and their associated user account.

    Permissions:
    - Only authenticated users with admin permissions can access this view.
    """ 

    try:
        selected_employee = Employee.objects.get(pk=employee_id)
        selected_user = selected_employee.user
    except Employee.DoesNotExist:
        logger.error(f"Employee ID {employee_id} not found")
        return Response({"error": "Employee not found"}, status=HTTP_404_NOT_FOUND)

    if request.method == "GET":

        serialized = EmployeeSerializer(selected_employee)
        return Response(serialized.data, status = HTTP_200_OK)
        
    if request.method == "PATCH":

        data = request.data.copy()

        # Separate Employee fields and User fields
        employee_fields = {"is_manager", "employee_status", "date_created", "manager_id"}
        user_fields = {"username", "first_name", "last_name", "email", "is_active", "is_staff"}

        employee_data = {key: data[key] for key in data if key in employee_fields}
        user_data = {key: data[key] for key in data if key in user_fields}

        if "manager_id" in data:
            manager_id = data["manager_id"]
            if manager_id:
                try:
                    manager = Employee.objects.get(pk=manager_id)
                    selected_employee.manager = manager  # Assign the Employee instance
                except Employee.DoesNotExist:
                    logger.error(f"Manager ID {manager_id} not found")
                    return Response({"error": "Manager not found"}, status=HTTP_400_BAD_REQUEST)
            else:
                employee_data["manager_id"] = None 

        # Update Employee model
        if employee_data:
            employee_serializer = EmployeeSerializer(selected_employee, data=employee_data, partial=True)
            if employee_serializer.is_valid():
                employee_serializer.save()
            else:
                return Response(employee_serializer.errors, status=HTTP_400_BAD_REQUEST)

        # Update User model
        if user_data:
            user_serializer = UserSerializer(selected_user, data=user_data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)

        logger.info(f"Successfully updated Employee ID: {employee_id}")
        return Response({"message": "Employee data updated successfully"}, status=HTTP_200_OK)
        

    if request.method == 'DELETE':
        user = selected_employee.user  # Get associated User
        selected_employee.delete()  # Delete Employee first
        if user:
            user.delete()  # Delete associated User
        return Response(
            {"message": "Removed an Employee", "Emp_id": employee_id},
            status=HTTP_200_OK
        )

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def new_employee(request):
    """
    Endpoint to create a new employee for admins.

    This endpoint allows an admin to create a new employee by first creating a user and then associating 
    them with an employee record.

    Permissions:
    - Only authenticated users with admin permissions can access this view.
    """

    if request.method == "POST":
        user_data = {
            "username": request.data.get('username'),
            "password1": request.data.get('password1'),
            "password2": request.data.get('password2'),
        }

        form = UserCreationForm(data = user_data)

        if form.is_valid():
            user = form.save(commit=False) # Create the user but don't save it yet
            user.is_staff = False
            user.is_superuser = False
            user.first_name = request.data.get("first_name", "")
            user.last_name = request.data.get("last_name", "")
            user.email = request.data.get("email", "")
            user.is_active = request.data.get("is_active", True)
            user.save()

            is_manager = request.data.get("is_manager", False)
            employee_status = request.data.get("employee_status", "Active").lower()
            manager_id = request.data.get("manager", None)

            manager = None  
            if manager_id:
                try:
                    manager = Employee.objects.get(id=manager_id)
                except Employee.DoesNotExist:
                    logger.error(f"Manager ID {manager_id} not found")
                    return Response({"error": "Manager not found!"}, status=HTTP_400_BAD_REQUEST)


            employee = Employee.objects.create(
                user = user,
                is_manager = is_manager,
                employee_status = employee_status.lower(),
                manager = manager,
                date_created = timezone.now()   
            )
            logger.info(f"Successfully created Employee ID: {employee.id}")
            return Response({"message": "Employee Created!", "employee_id": employee.id}, status=HTTP_200_OK)
        else:
            logger.error(f"User creation failed: {form.errors}")
            return Response(form.errors, status=HTTP_400_BAD_REQUEST)



    #------------------------------------------------Manager-----------------------------------------------------------#

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsManager])
def listing_requests_manager(request):
    """
    Endpoint for managers to view requests submitted by employees they manage.

    This endpoint allows managers to filter and sort requests based on status, date range, and employee name.

    Permissions:
    - Only authenticated users with manager permissions can access this view.

    """
    if request.method == "GET":
        try:
            manager = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            logger.error("Manager not found for the logged-in user")
            raise AuthenticationFailed("User does not have an associated Employee.") #logged in employee


        status_filter = request.query_params.get('status')  
        sort_option = request.query_params.get('sort_by')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        search_name = request.query_params.get('search_name')

        data = Request.objects.filter(employee__manager=manager) #filter first, by looking up thru employee->manager->manager=maanger
        data = data.select_related('employee__user','manager__user') #Django joins the Request, Employee, and User tables in one SQL query
        
        if status_filter:
            data = data.filter(status_of_request=status_filter)

        if start_date and end_date:
            data = data.filter(date_of_request__range=[start_date, end_date])
        elif start_date:
            data = data.filter(date_of_request__gte=start_date)  # Greater than or equal to start_date
        elif end_date:
            data = data.filter(date_of_request__lte=end_date)  # Less than or equal to end_date # Date range filtering

        if search_name:
            data = data.filter(
                            Q(employee__user__first_name__icontains=search_name) |
                            Q(employee__user__last_name__icontains=search_name)
                )
        
        valid_sort_options = ['date_of_request', 'from_date']
        if sort_option:
            descending = sort_option.startswith('-')
            clean_sort_option = sort_option.lstrip('-')  

            if clean_sort_option in valid_sort_options:
                data = data.order_by(f"-{clean_sort_option}" if descending else clean_sort_option)


        if not data.exists():
            logger.error("No requests found")
            return Response({'message': "No requests found"}, status=HTTP_404_NOT_FOUND)

        serialized = TravelSerializer(data, many=True)
        return Response(serialized.data, status=HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManager])
def action_request_manager(request,request_id):
    """
    Endpoint for managers to take action on a specific request made by an employee.

    Permissions:
    - Only authenticated users with manager permissions can access this view.

    """
    if request.method == 'POST':
        
        try:
            selected_request = Request.objects.get(pk=request_id)
        except Request.DoesNotExist:
            logger.error(f"Request ID {request_id} not found")
            return Response({"error": "Request not found"}, status=HTTP_404_NOT_FOUND)

        action  = request.data.get('action')
        note = request.data.get('note')

        if selected_request.status_of_request == "submitted":
            if not action or action not in ["approve", "reject", "revert"]:
                return Response({"message":"Invalid action"}, status = HTTP_404_NOT_FOUND)

            if action == "approve":
                selected_status = "approved"
                date = "date_of_approval"
            elif action == "reject":
                selected_status = "rejected"
                date = "date_of_rejection"
            elif action == "revert":
                selected_status = "reverted"
                date = "date_of_revert"
                selected_request.resubmission_request = True
            
            subject = f'Request {selected_status}'
            message = f'Note:{note} \n Your request for travel has been {selected_status}. Thanks & Regards. - Admin'
            from_email = 'umersaleh30570@gmail.com'  
            recipient_list = [selected_request.employee.user.email]  

            serialized = TravelSerializer(
                selected_request,
                data={ 
                    "status_of_request": selected_status,
                    date: now().date(),
                    "message_from_manager": note 
                },
                partial=True
            )
                        
            if serialized.is_valid():
                serialized.save()
                send_mail(subject, message, from_email, recipient_list)
            else:
                return Response(serialized.errors,status = HTTP_400_BAD_REQUEST)

            return Response({"message":"status updated","action":action},status = HTTP_200_OK)

        else:
            logger.error(f"Cannot proceed with action on Request ID {request_id}")
            return Response({"error":"Cannot Proceed with the action!"},status = HTTP_400_BAD_REQUEST)


#-----------------------------------------------------------Employee------------------------------------------------------------#

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsEmployee])
def listing_requests_employee(request):
    """
    Endpoint for employees to list their requests.

    Permissions:
    - Only authenticated users with employee permissions can access this view.
    - If the employee is a manager, they will be denied access.

    Query Parameters:
    - 'purpose_of_travel': Filter requests by purpose of travel.
    
    """
    if request.method == "GET":
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            logger.warning(f"Employee not found for user: {request.user}")
            raise AuthenticationFailed("Employee does not exist.") 

        if employee.is_manager == 1:
            return Response({"message": "Manager cannot make requests."}, status=HTTP_404_NOT_FOUND)

        data = Request.objects.filter(employee=employee)

        search_purpose = request.query_params.get('purpose_of_travel')
        if search_purpose:
            data = data.filter(purpose_of_travel__icontains=search_purpose)
        
        if not data.exists():
            logger.error("No requests found")
            return Response({"message": "No requests found."}, status=HTTP_404_NOT_FOUND)

        serialized = TravelSerializer(data, many=True)

        return Response(serialized.data, status=HTTP_200_OK)


@api_view(["PATCH"])   
@permission_classes([IsAuthenticated, IsEmployee])
def edit_request_employee(request,request_id):
    """
    Endpoint for employees to edit their own requests.

    Permissions:
    - Only authenticated users with employee permissions can access this view.
    - The employee can only edit their own requests.

    """
    if request.method == "PATCH":
        try:
            selected_request = Request.objects.get(pk=request_id)
        except Request.DoesNotExist:
            return Response({"error": "Request not found"}, status=HTTP_404_NOT_FOUND)


        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            raise AuthenticationFailed("Employee does not exist.")

        if selected_request.employee != employee:
            return Response({"error": "You do not have permission to edit this request"}, status=HTTP_400_BAD_REQUEST)

        serialized = TravelSerializer(selected_request, data = request.data, partial = True)
        
        if serialized.is_valid():
            serialized.save()
        else:
            return Response(serialized.errors, status = HTTP_404_NOT_FOUND)
        
        return Response(serialized.data , status = HTTP_200_OK)


@api_view(['POST','DELETE'])
@permission_classes([IsAuthenticated, IsEmployee])
def action_request_employee(request,request_id):
    """
    Handle actions on employee requests like submitting or deleting the request.
    POST - Submit a request if eligible.
    DELETE - Delete a request if eligible.

    """
    if request.method == 'POST':
        try:
            selected_request = Request.objects.get(pk=request_id)
        except Request.DoesNotExist:
            return Response({"error": "Request not found"}, status=HTTP_404_NOT_FOUND)

        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response({"error": "Employee does not exist  ."}, status=HTTP_400_BAD_REQUEST)

        if not selected_request.employee or selected_request.employee is None:
            return Response({"error": "You do not have an employee owning this."}, status=HTTP_400_BAD_REQUEST)

        if selected_request.employee != employee:
            return Response({"error": "You do not have permission to perform this action."}, status=HTTP_400_BAD_REQUEST)

        action  = request.data.get('action')

        if action != "submit":
            return Response({"message": "Invalid action"}, status=HTTP_400_BAD_REQUEST)

        if selected_request.status_of_request not in ["to_submit", "reverted"]:
            return Response({"message": "Invalid action"}, status=HTTP_400_BAD_REQUEST)


        if selected_request.status_of_request == 'reverted':
            selected_request.is_resubmitted = True
            
            selected_request.save()  

        
        selected_status = "submitted"

        if selected_request.status_of_request == 'reverted':
            subject = f'Request {selected_status} from employee-{employee.id}'
            message = f'I have {selected_status} a request for travel. Please look into the details. Thanks & Regards. - Admin'
            from_email = 'umersaleh30570@gmail.com'  
            recipient_list = [selected_request.manager.user.email]  
        else:
            subject = f'Request re{selected_status} from employee-{employee.id}'
            message = f'I have re{selected_status} a request for travel. Please look into the details. Thanks & Regards. - Admin'
            from_email = 'umersaleh30570@gmail.com'  
            recipient_list = [selected_request.manager.user.email]  

        
        
        serialized = TravelSerializer(selected_request, data = { "status_of_request" : selected_status }, partial=True)

        if serialized.is_valid():
            serialized.save()
            send_mail(subject, message, from_email, recipient_list)
        else:
            return Response(serialized.errors,status = HTTP_400_BAD_REQUEST)

        return Response({"message":"status updated","action":action},status = HTTP_200_OK)

    if request.method == 'DELETE':  
        try:
            selected_request = Request.objects.get(pk=request_id)
        except Request.DoesNotExist:
            logger.error("Request not found")
            return Response({"error": "Request not found"}, status=HTTP_404_NOT_FOUND)

        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            logger.error("Request not found")
            return Response({"error": "Employee does not exist."}, status=HTTP_400_BAD_REQUEST)

        if not selected_request.employee or selected_request.employee is None:
            logger.error("You do not have an employee owning this.")
            return Response({"error": "You do not have an employee owning this."}, status=HTTP_400_BAD_REQUEST)



        if selected_request.employee != employee:
            return Response({"error": "You do not have permission to perform this action."}, status=HTTP_400_BAD_REQUEST)
        
        selected_request.delete()
        return Response({"message":"deleted request","request":request_id},status = HTTP_200_OK)



@api_view(["POST"])
@permission_classes([IsAuthenticated, IsEmployee])
def emp_request_form(request):
    """
        Submit an employee request form.
        
        This function will associate the logged-in employee with the request being made.
        It serializes the request data, saves it with the employee and manager info, 
        and returns a success message if the submission is successful.
        
    """
    if request.method == "POST":
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            raise AuthenticationFailed("Employee does not exist.")

        manager = employee.manager

        data = request.data.copy()  
        serialized = TravelSerializer(data = data)
        
        subject = f'Request submitted from employee-{employee.id}'
        message = f'I have submitted a request for travel. Please look into the details. Thanks & Regards. - Admin'
        from_email = 'umersaleh30570@gmail.com'  
        recipient_list = [manager.user.email]  

        if serialized.is_valid():
            serialized.save(employee=employee, manager=manager, status_of_request="submitted")
            send_mail(subject, message, from_email, recipient_list)
        else:
            return Response(serialized.errors, status = HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Request Submitted'},status = HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Ensure user is authenticated
def get_logged_in_employee_details(request):
    try:
        employee = Employee.objects.get(user=request.user)

        # Get Employee's Full Name (fallback to username)
        employee_name = f"{employee.user.first_name} {employee.user.last_name}".strip() or employee.user.username

        # Get Manager's Full Name (if assigned)
        if employee.manager:
            manager = employee.manager.user  # Assuming Manager is linked to User model
            manager_name = f"{manager.first_name} {manager.last_name}".strip() or manager.username
        else:
            manager_name = "No Manager"

        return Response({
            "id": employee.id,
            "employee_name": employee_name,
            "manager_name": manager_name
        })

    except Employee.DoesNotExist:
        return Response({"error": "Employee details not found"}, status=HTTP_404_NOT_FOUND)

@api_view(['POST'])
def employee_login(request):
    """
    Handle employee login and return an authentication token.
    
    Parameters:
        username (str): The employee's username.
        password (str): The employee's password.
    
    Returns:
        Response: HTTP response with the status and token if successful.
    """

    if request.method == "POST":
        username = request.data.get('username')
        password = request.data.get('password')

        if not (username and password):
            return Response({"message":"Please enter both the fields"}, status= HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            return Response({"User Does Not Exist"},status = HTTP_404_NOT_FOUND)

        try:
            employee = Employee.objects.get(user=user)
            if not employee.is_manager and not user.is_superuser:
                token, _ = Token.objects.get_or_create(user = user)
                logger.info(f"Token generated for employee")
                return Response({"Token Generated":token.key},status = HTTP_200_OK)
            else:
                return Response({"message": "Please login from Manager/Admin Portal"}, status=HTTP_400_BAD_REQUEST)
        except Employee.DoesNotExist:
            logger.error("You don't have an employee record.")
            return Response({"error": "You don't have an employee record."}, status=HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def manager_login(request):
    """
    Handle manager login and return an authentication token.
    
    Parameters:
        username (str): The manager's username.
        password (str): The manager's password.
    
    Returns:
        Response: HTTP response with the status and token if successful.
    """

    if request.method == "POST":
        username = request.data.get('username')
        password = request.data.get('password')

        if not (username and password):
            return Response({"message":"Please enter both the fields"}, status= HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            return Response({"error":"User Does Not Exist"},status = HTTP_404_NOT_FOUND)

        try:
            employee = Employee.objects.get(user=user)
            if employee.is_manager:
                token, _ = Token.objects.get_or_create(user = user)
                logger.info(f"Token generated for manager")
                return Response({"Token Generated":token.key},status = HTTP_200_OK)
            else:
                logger.info("Please login from Employee/Admin Portal")
                return Response({"message": "Please login from Employee/Admin Portal"}, status=HTTP_400_BAD_REQUEST)
        except Employee.DoesNotExist:
            logger.error("This user is not associated with an employee record.")
            return Response({"error": "This user is not associated with an employee record."}, status=HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def admin_login(request):
    """
    Handle admin login and return an authentication token.
    
    Parameters:
        username (str): The admin's username.
        password (str): The admin's password.
    
    Returns:
        Response: HTTP response with the status and token if successful.
    """

    if request.method == "POST":
        username = request.data.get('username')
        password = request.data.get('password')

        if not (username and password):
            return Response({"message":"Please enter both the fields"}, status= HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            return Response({"error": "User Does Not Exist"}, status=HTTP_404_NOT_FOUND)

        if user.is_superuser:
            token, _ = Token.objects.get_or_create(user = user)
            logger.info(f"Token generated for admin")
            return Response({"Token Generated":token.key},status = HTTP_200_OK)
        else: 
            return Response({"message": "Please login from Manager/Employee Portal"}, status=HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_admin(request):
    """
    Create a new admin user and associate it with an admin role.
    
    Parameters:
        request (dict): The user details (username, password, etc.) to create a new admin.
    
    Returns:
        Response: HTTP response with the status and admin creation message.
    """
    if request.method == 'POST':
        # Using UserCreationForm to handle password hashing
        form = UserCreationForm(data=request.data)
        
        if form.is_valid():
            user = form.save(commit=False)  
            user.is_superuser = True  # Make user an admin
            user.is_staff = True  # Allow access to admin panel
            user.save()  # Save user with hashed password
            
            # Create the Admin entry linked to the user
            admin = Admin.objects.create(user=user)
            logger.info(f"Admin {admin.id} created successfully")
            return Response({"message": "Admin Created!", "admin_id": admin.id}, status=HTTP_200_OK)
        else:
            logger.error(f"Admin creation failed: {form.errors}")
            return Response(form.errors, status=HTTP_400_BAD_REQUEST)



