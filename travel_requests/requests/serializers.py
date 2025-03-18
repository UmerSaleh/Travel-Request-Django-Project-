from . import models
from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the Django built-in User model.

    This serializer converts User model instances into JSON format and vice versa.
    It includes all fields from the User model.

    Meta:
        model (User): The Django built-in User model.
        fields (str): Specifies that all fields should be serialized.
    """

    class Meta:
        model = User
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Employee model.

    This serializer includes the related User model serializer to provide 
    username and password fields within the Employee serializer.

    Attributes:
        user (UserSerializer): Nested serializer to include user-related fields.
    
    Meta:
        model (Employee): The Employee model.
        fields (str): Specifies that all fields should be serialized.
    """
    user = UserSerializer()

    class Meta:
        model = models.Employee
        fields = '__all__'

    # def create(self, data):
    #     """
    #     Handle nested creation of User and Employee objects.
    #     """
    #     user_data = data.pop('user')  # Renamed 'validated_data' to 'data'
    #     user = models.User.objects.create(**user_data)
    #     employee = models.Employee.objects.create(user=user, **data)

class AdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the Admin model.

    This serializer includes the related User model serializer 
    to provide user-related fields within the Admin serializer.

    Attributes:
        user (UserSerializer): Nested serializer to include user-related fields.
    
    Meta:
        model (Admin): The Admin model.
        fields (str): Specifies that all fields should be serialized.
    """
    user = UserSerializer()

    class Meta:
        model = models.Admin
        fields = '__all__'


class TravelSerializer(serializers.ModelSerializer):
    """
    Serializer for the Travel Request model.

    This serializer includes nested Employee serializers for both 
    the employee making the request and the manager handling it.

    Attributes:
        employee (EmployeeSerializer): Read-only nested serializer for employee details.
        manager (EmployeeSerializer): Read-only nested serializer for manager details.

    Meta:
        model (Request): The Request model representing travel requests.
        fields (str): Specifies that all fields should be serialized.
    """

    employee = EmployeeSerializer(read_only=True)  
    manager = EmployeeSerializer(read_only=True)  

    class Meta:
        model = models.Request
        fields = '__all__'

    def validate(self, data):
        """
        Custom validation logic for travel requests.

        - Ensures 'from_date' is earlier than 'to_date'.
        - Validates that 'lodging_info' is provided if 'lodging' is True.
        - Ensures that the 'employee' and 'manager' are not the same.

        Raises:
            serializers.ValidationError: If any of the validation checks fail.

        Returns:
            dict: Validated data.
        """
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        lodging = data.get('lodging')
        lodging_info = data.get('lodging_info')
        employee = data.get('employee')
        manager = data.get('manager')

        # Validate that 'from_date' is before 'to_date'
        if from_date and to_date and from_date >= to_date:
            raise serializers.ValidationError({"date_error": "From date must be earlier than To date."})

        # Validate lodging info if lodging is required
        if lodging and not lodging_info:
            raise serializers.ValidationError({"lodging_info": "Lodging details are required when lodging is requested."})

        # Ensure employee and manager are not the same
        if employee and manager and employee == manager:
            raise serializers.ValidationError({"manager_error": "Employee cannot be their own manager."})

        return data