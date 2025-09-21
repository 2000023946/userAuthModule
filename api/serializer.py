from rest_framework import serializers # type: ignore
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from .validators import *


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'full_name', 'password']

    def validate_username(self, value):
        return UsernameValidator().validate(value)
    
    def validate_email(self, value):
        return EmailValidator().validate(value)
    
    def validate_password(self, value):
        return PasswordValidator().validate(value)
    
    def validate(self, data):
        return UserRegistrationValidator().validate(data)
    

