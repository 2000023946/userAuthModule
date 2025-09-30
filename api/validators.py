import re
from abc import ABC

from api.models import CustomUser


class ValidationError(ValueError):
    pass


class Validable(ABC):
    def validate(self, value, all_data=None):
        """
        Return True if value is valid, otherwise raise ValidationError.
        """
        True

    def _ensure_str(self, value, field_name="Value"):
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string.")

    def _validate_all_data(self, all_data):
        if not all_data:
            raise ValidationError("DATA can't be empty")
        for k, v in all_data.items():
            if not v:
                raise ValidationError(f"Field '{k}' cannot be empty.")


class DefaultValidator(Validable):
    pass


class UsernameValidator(Validable):
    def validate(self, value, all_data=None):
        self._ensure_str(value, "Username")
        if not (3 <= len(value) <= 30):
            raise ValidationError("Username must be 3-30 characters.")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", value):
            raise ValidationError(
                "Username can only contain letters, numbers, underscores, dots, or hyphens."
            )
        if CustomUser.objects.filter(username=value).exists():
            raise ValidationError("Username is already taken.")
        return True


class EmailValidator(Validable):
    def validate(self, value, all_data=None):
        self._ensure_str(value, "Email")
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", value):
            raise ValidationError("Invalid email address.")
        print('validating the email', value, CustomUser.objects.all(), CustomUser.objects.filter(email=value).exists(),)
        if CustomUser.objects.filter(email=value).exists():
            raise ValidationError("Email is already registered.")
        return True


class PasswordValidator(Validable):
    def validate(self, value, all_data=None):
        self._ensure_str(value, "Password")
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        if not re.search(r"\d", value):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r"[A-Z]", value):
            raise ValidationError(
                "Password must contain at least one uppercase letter."
            )
        return True


class PasswordRepeatValidator(Validable):
    def validate(self, value, all_data=None):
        original = (all_data or {}).get("password")
        if value != original:
            raise ValidationError("Passwords do not match.")
        return True


class EmailResetValidator(Validable):
    def validate(self, value, all_data=None):
        self._ensure_str(value, "Email")
        if not CustomUser.objects.filter(email=value).exists():
            raise ValidationError("No user found with this email.")
        return True


class UserRegistrationValidator(Validable):
    def validate(self, value, all_data=None):
        self._validate_all_data(all_data or {})

        username = all_data.get("username")
        email = all_data.get("email")
        if not username or not email:
            raise ValidationError("Username and email must be provided.")

        if (
            username.lower() in email.lower()
            or email.split("@")[0].lower() in username.lower()
        ):
            raise ValidationError("Username and email are too similar.")
        return True


class PasswordResetValidator(Validable):
    def validate(self, value, all_data=None):
        self._validate_all_data(all_data or {})
        return True


