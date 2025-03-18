from django.db import models
from django.contrib.auth.models import User

class Admin(models.Model):
    """
    Represents an admin user linked to the built-in Django User model.

    Attributes:
        user (User): A one-to-one relationship with the Django User model,
                     ensuring each admin has a corresponding user account.
    """
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='admin_profile'
    )

class Employee(models.Model):
    """
    Represents an employee, linked to the Django User model.

    Attributes:
        user (User): A one-to-one relationship with the Django User model,
                     ensuring each employee has a corresponding user account.
        is_manager (bool): Indicates if the employee is a manager.
        manager (Employee): A foreign key referring to another employee who is the manager.
        employee_status (str): The status of the employee (active, inactive, or terminated).
        date_created (date): The date the employee record was created.
    """
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    is_manager = models.BooleanField(default=False)
    manager = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    EMPLOYEE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
    ]
    employee_status = models.CharField(
        max_length=20, 
        choices=EMPLOYEE_STATUS_CHOICES, 
        default='active'
    )
    date_created = models.DateField()


class Request(models.Model):
    """
    Represents a travel request made by an employee to a manager.

    Attributes:
        employee (Employee): The employee submitting the request.
        manager (Employee): The manager reviewing the request.
        purpose_of_travel (str): The reason for travel.
        mode_of_travel (str): The mode of transportation chosen.
        from_date (date): The starting date of travel.
        to_date (date): The ending date of travel.
        from_where (str): The departure location.
        to_where (str): The destination.
        lodging (bool): Indicates if lodging is required.
        lodging_info (str): Additional lodging details.
        additional_request (str): Extra requests made by the employee.
        additional_info (str): Additional details related to the request.
        message_from_manager (str): A message from the manager regarding the request.
        message_from_admin (str): A message from the admin regarding the request.
        date_of_request (date): The date the request was made.
        date_of_approval (date): The date the request was approved.
        date_of_rejection (date): The date the request was rejected.
        date_of_revert (date): The date the request was reverted.
        resubmission_request (bool): Indicates if a resubmission was requested.
        is_resubmitted (bool): Indicates if the request was resubmitted.
        status_of_request (str): The current status of the request.
    """
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        related_name='requests_sent', 
        blank=True, 
        null=True
    )
    manager = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        related_name='requests_received', 
        blank=True, 
        null=True
    )
    purpose_of_travel = models.CharField(max_length=100)
    MODE_CHOICES = [
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('own vehicle', 'Own Vehicle'),
        ('ship', 'Ship')
    ]
    mode_of_travel = models.CharField(max_length=100, choices=MODE_CHOICES)
    from_date = models.DateField()
    to_date = models.DateField()
    from_where = models.CharField(max_length=100)
    to_where = models.CharField(max_length=100)
    lodging = models.BooleanField(default=False)
    lodging_info = models.CharField(max_length=100, blank=True, null=True)
    additional_request = models.CharField(max_length=500, blank=True, null=True)
    additional_info = models.CharField(max_length=500, blank=True, null=True)
    message_from_manager = models.CharField(max_length=300, blank=True, null=True)
    message_from_admin = models.CharField(max_length=300, blank=True, null=True)
    date_of_request = models.DateField(auto_now_add=True)
    date_of_approval = models.DateField(blank=True, null=True)
    date_of_rejection = models.DateField(blank=True, null=True)
    date_of_revert = models.DateField(blank=True, null=True)
    resubmission_request = models.BooleanField(default=False)
    is_resubmitted = models.BooleanField(default=False)
    STATUS_CHOICES = [
        ("to_submit", "To Submit"),
        ("submitted", "Submitted"),
        ("rejected", "Rejected"),
        ("reverted", "Reverted"),
        ("approved", "Approved"),
        ("closed", "Closed"),
    ]
    status_of_request = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="to_submit"
    )


