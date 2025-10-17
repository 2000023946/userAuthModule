from abc import ABC, abstractmethod
from django_redis import get_redis_connection
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from api.models import CustomUser
from .serializer import UserSerializer

from .utils import (
    blacklist_refresh,
    blacklist_access,
    get_user_by_email,
    get_user_by_id,
)

from .tracers import trace
from .o_auth_start import ThirdPartyStrategySingleton

# ------------------------------------------------------------------
# 1. CORE INTERFACES
# ------------------------------------------------------------------


class BuilderException(Exception):
    pass


class Buildable(ABC):
    @abstractmethod
    @trace(lambda self: f"{self.__class__.__name__}_post")
    def build(self, data):
        pass


class Cleanable(ABC):
    @property
    @abstractmethod
    def cleaners(self):
        pass


class Serializable(ABC):
    @abstractmethod
    def get_serializer(self, instance=None, data=None):
        pass


class Updatable(ABC):
    @abstractmethod
    def get_instance(self, data):
        pass


# ------------------------------------------------------------------
# 2. MODEL BUILDERS
# ------------------------------------------------------------------


class ModelBuilder(Buildable, Cleanable, Serializable, ABC):
    """Base builder for creating/updating models."""

    serializer_class = None

    def get_serializer(self, instance=None, data=None):
        """Returns an instance of the serializer."""
        if instance and data:
            return self.serializer_class(instance, data=data)
        if instance:
            return self.serializer_class(instance)
        if data:
            return self.serializer_class(data=data)
        return self.serializer_class()

    def build(self, data):
        cleaned_data = self.clean(data)
        instance = self.perform_build(cleaned_data)
        serializer = self.get_serializer(instance=instance)
        return serializer.data

    def clean(self, data):
        for cleaner_class in self.cleaners:
            data = cleaner_class().clean(data)
        return data

    @abstractmethod
    def perform_build(self, data):
        pass


class CreateModelBuilder(ModelBuilder):
    """Creates new model instances."""

    def perform_build(self, data):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


class UpdateModelBuilder(ModelBuilder, Updatable):
    """Updates existing model instances."""

    def perform_build(self, data):
        print("perforing the build", data)
        instance = self.get_instance(data)
        print("instance")
        serializer = self.get_serializer(instance=instance, data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


# ------------------------------------------------------------------
# 3. CLEANER STRATEGIES
# ------------------------------------------------------------------


class Clean(ABC):
    @abstractmethod
    def clean(self, data):
        pass


class UserPasswordCleaner(Clean):
    def clean(self, data):
        if "password_repeat" in data:
            data["password"] = data["password_repeat"]
            del data["password_repeat"]

        return data


# ------------------------------------------------------------------
# 4. CONCRETE MODEL BUILDERS
# ------------------------------------------------------------------


class UserBuilder(CreateModelBuilder):
    name = "UserBuilder"
    serializer_class = UserSerializer
    cleaners = [UserPasswordCleaner]


class PasswordResetBuilder(UpdateModelBuilder):
    name = "PasswordResetBuilder"
    serializer_class = UserSerializer
    cleaners = [UserPasswordCleaner]

    def get_instance(self, data):
        print("getting the instance", data)
        email = data["email"]
        user = get_user_by_email(email=email)
        print("getting the instance", user)
        return user


# ------------------------------------------------------------------
# 5. API RESPONSE BUILDERS
# ------------------------------------------------------------------


class APIResponseBuilder(Buildable, ABC):
    """Base builder for API responses (non-model data)."""

    pass


class LoginBuilder(APIResponseBuilder):
    """Builds a JWT token response."""

    def build(self, data):
        user = self.get_instance(data)
        print("user ", user)
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return {
            "refresh": str(refresh),
            "access": str(access),
        }

    def get_instance(self, data):
        return get_user_by_email(email=data["email"])


class ValidationTokenBuilder(APIResponseBuilder):
    """Validates a JWT token."""

    def build(self, data):
        token = data.get("refresh_token")
        if not token:
            raise BuilderException("Token not provided.")
        try:
            RefreshToken(token)
            return {"detail": "Token is valid."}
        except TokenError:
            raise BuilderException("Token is invalid or expired.")


class LogoutBuilder(APIResponseBuilder):
    """Invalidates tokens by blacklisting them."""

    def build(self, data):
        print("logout data", data)
        refresh_token = data.get("refresh")
        access_token = data.get("access")
        if not refresh_token or not access_token:
            raise BuilderException("Both access and refresh tokens must be provided.")

        try:
            conn = get_redis_connection("default")

            blacklist_refresh(conn, refresh_token)

            blacklist_access(conn, refresh_token)

            return {"detail": "Logout successful. Tokens invalidated."}
        except Exception:
            raise BuilderException("An unexpected error occurred during logout.")


class TokenRefreshBuilder(LoginBuilder):
    """Refreshes JWT tokens."""

    class MinimalUser:
        def __init__(self, id):
            self.id = id

    def build(self, data):
        refresh_token = data.get("refresh")
        print(refresh_token, "token 56")
        if not refresh_token:
            raise BuilderException("Refresh token not provided.")
        try:
            conn = get_redis_connection("default")
            print("got the conn")

            user_id = refresh_token.get("user_id")

            print("user id", user_id)

            blacklist_refresh(conn, refresh_token)

            print("balcklisted")
            return super().build({"pk": user_id})
        except (TokenError, CustomUser.DoesNotExist):
            raise TokenError("Token is invalid or user not found.")
        except Exception:
            raise BuilderException("An unexpected error occurred during token refresh.")

    def get_instance(self, data):
        print(data, "gettingthe user")
        return get_user_by_id(data["pk"])


class OAuthUserInfoBuilder(APIResponseBuilder):
    def build(self, data):
        provider = data.get("provider")
        token = data.get("token")

        if not provider or not token:
            raise BuilderException("Inputs where not given. Cannot be null!")

        user_info = ThirdPartyStrategySingleton.get_user_info(provider, token)
        return user_info
