from rest_framework.permissions import BasePermission
from .models import Employee 
from django.core.exceptions import ObjectDoesNotExist

class IsAdmin(BasePermission):
    """
    Custom permission to allow access only to admin users (Django superusers).

    Methods:
        has_permission(request, view): Returns True if the user is authenticated
                                       and is a superuser.
    """

    def has_permission(self, request, view):
        """
        Check if the request user is authenticated and is a superuser.

        Args:
            request : The request instance.
            view (APIView): The view being accessed.

        Returns:
            bool: True if the user is authenticated and a superuser, else False.
        """
        return request.user.is_authenticated and request.user.is_superuser

class IsManager(BasePermission):
    """
    Custom permission to allow access only to manager users.

    Methods:
        has_permission(request, view): Returns True if the user is authenticated
                                       and has an associated Employee profile
                                       with `is_manager` set to True.
    """

    def has_permission(self, request, view):
        """
        Check if the request user is authenticated and is a manager.

        Args:
            request: The request instance.
            view (APIView): The view being accessed.

        Returns:
            bool: True if the user is authenticated and is a manager, else False.
        """
        if not request.user.is_authenticated:
            return False

        try:
            employee = Employee.objects.get(user=request.user)
            return employee.is_manager
        except Employee.DoesNotExist:
            return False  # Deny access if no Employee profile exists

class IsEmployee(BasePermission):
    """
    Custom permission to allow access only to non-manager employees.

    Methods:
        has_permission(request, view): Returns True if the user is authenticated
                                       and has an associated Employee profile
                                       with `is_manager` set to False.
    """

    def has_permission(self, request, view):
        """
        Check if the request user is authenticated and is a non-manager employee.

        Args:
            request (HttpRequest): The request instance.
            view (APIView): The view being accessed.

        Returns:
            bool: True if the user is authenticated and is a non-manager employee, else False.
        """
        if not request.user.is_authenticated:
            return False

        try:
            employee = Employee.objects.get(user=request.user)
            return not employee.is_manager
        except Employee.DoesNotExist:
            return False  # Deny access if no Employee profile exists