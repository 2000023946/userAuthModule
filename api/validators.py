import re
from abc import ABC
from tokenize import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

import jwt
from django_redis import get_redis_connection
from django.contrib.auth.hashers import check_password

from UserAuthModule import settings
from api.models import CustomUser
from .cache import QueryCacheSingleton
from .utils import get_user_by_email
from .o_auth_start import ThirdPartyStrategySingleton
from .tracers import trace


class ValidationError(ValueError):
    pass


class Validable(ABC):
    @trace(lambda self: f"{self.__class__.__name__}_validate")
    def validate(self, value):
        """
        Return True if value is valid, otherwise raise ValidationError.
        """
        True


class StateValidator(Validable, ABC):
    def validate(self, value):
        """
        Return True if value is valid, otherwise raise ValidationError.
        """
        True

    def _ensure_str(self, value, field_name="Value"):
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string.")


class CompleteStateValidator(Validable, ABC):
    def validate(self, value):
        """
        Return True if value is valid, otherwise raise ValidationError.
        Value is all the data in the Complete
        """
        True

    def _validate_all_data(self, all_data):
        if not all_data:
            raise ValidationError("DATA can't be empty")
        for k, v in all_data.items():
            if not v:
                raise ValidationError(f"Field '{k}' cannot be empty.")


class DefaultStateValidator(StateValidator):
    pass


class UsernameValidator(StateValidator):
    def validate(self, value):
        self._ensure_str(value, "Username")

        if not (3 <= len(value) <= 30):
            raise ValidationError("Username must be 3-30 characters.")

        if not re.match(r"^[a-zA-Z0-9_.-]+$", value):
            raise ValidationError(
                "Username can only contain letters, numbers, underscores, dots, or hyphens."
            )

        # Use query cache
        def query_username():
            return CustomUser.objects.filter(username=value).exists()

        if QueryCacheSingleton.get_or_set(f"username:{value}", query_username):
            raise ValidationError("Username is already taken.")

        return True


class EmailValidator(StateValidator):
    def validate(self, value):
        self._ensure_str(value, "Email")

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", value):
            raise ValidationError("Invalid email address.")

        if get_user_by_email(value):
            raise ValidationError("Email is already registered.")

        return True


class PasswordValidator(StateValidator):
    def validate(self, value):
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


class EmailResetValidator(StateValidator):
    def validate(self, value):
        self._ensure_str(value, "Email")
        user = get_user_by_email(value, cache_key_prefix="email_reset")
        if not user:
            raise ValidationError("No user found with this email.")
        return True


# ------------------------------------------------------------------
# ADVANCED TOKEN VALIDATORS
# ------------------------------------------------------------------


class TokenValidator(StateValidator):
    """
    A base validator for JWTs. Performs preliminary, stateless checks
    on the token's format.
    """

    def validate(self, value):
        """
        Validates that the token is a non-empty string in a plausible JWT format.
        """
        self._ensure_str(value, "Token")

        if not value:
            raise ValidationError("Token cannot be empty.")

        # A simple check to ensure the token looks like a JWT (header.payload.signature)
        # More complex validation (signature, expiration) is handled by the JWT library
        # in the service layer.
        if value.count(".") != 2:
            raise ValidationError("Invalid token format.")

        return True


class AccessTokenValidator(StateValidator):
    """
    Performs a full validation on an access token.
    Checks signature, expiration, and blacklist status.
    """

    def validate(self, value):
        self._ensure_str(value, "Access Token")
        if not value:
            raise ValidationError("Access token cannot be empty.")

        print("not null token")

        # Check blacklist in Redis
        conn = get_redis_connection("default")
        if conn.get(f"blacklisted_token:{value}"):
            raise ValidationError("Token has been blacklisted (logged out).")

        print("not in the blacklist")

        try:
            # The jwt.decode function automatically validates the signature
            # and the expiration ('exp') claim.
            jwt.decode(value, settings.SECRET_KEY, algorithms=["HS256"])
            print("decoded check")
        except jwt.ExpiredSignatureError:
            raise ValidationError("Access token has expired.")
        except jwt.InvalidTokenError:
            raise ValidationError("Access token is invalid or has a bad signature.")

        return True


class RefreshTokenValidator(StateValidator):
    """
    Performs a full validation on a refresh token.
    Uses the SimpleJWT library for convenience.
    """

    def validate(self, value):
        self._ensure_str(value, "Refresh Token")
        if not value:
            raise ValidationError("Refresh token cannot be empty.")

        # Check blacklist in Redis
        conn = get_redis_connection("default")
        if conn.get(f"blacklisted_token:{value}"):
            raise ValidationError("Token has been blacklisted (logged out).")

        print("refresh not blacklist ")

        print("value,", value)

        try:
            # The RefreshToken class from simple-jwt handles all validation
            # including signature, expiration, and token type.
            RefreshToken(value)
            print("good refresh")
        except TokenError as e:
            # Catch the specific exception from the library
            raise ValidationError(str(e))

        return True


class ProviderValidator(StateValidator):
    def validate(self, value):
        print("validtign", value)
        if not value:
            raise ValidationError("Provider cannot be null")
        if value not in ThirdPartyStrategySingleton.strategies:
            raise ValidationError("Provider entered not in the list of providers")
        return True


class OAuthTokenValidator(StateValidator):
    def validate(self, value):
        if not value:
            raise ValidationError("Token cannot be empty")
        return True


class UserRegistrationValidator(CompleteStateValidator):
    def validate(self, all_data):
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
        # check the password and the password_repeat
        return PasswordResetValidator().validate(all_data)


class PasswordResetValidator(CompleteStateValidator):
    def validate(self, all_data):
        print(all_data)
        self._validate_all_data(all_data or {})
        password = all_data.get("password")
        password_repeat = all_data.get("password_repeat")
        if not check_password(password_repeat, password):
            raise ValidationError("Passwords do not match.")
        print("passwords match")
        return True


class TokenRefreshValidator(CompleteStateValidator):
    def validate(self, all_data):
        return True
