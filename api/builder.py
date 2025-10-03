from abc import ABC, abstractmethod
import datetime

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import CustomUser
from .serializer import UserSerializer


# ------------------------------------------------------------------
# 1. CORE & INTERFACE ABCs (Excellent for ISP)
# ------------------------------------------------------------------


class Buildable(ABC):
    """The absolute base contract for any builder."""

    @abstractmethod
    def build(self):
        pass

    def register(self, key, value):
        self.data[key] = value


class Cleanable(ABC):
    """An interface for objects that use composable cleaner strategies."""

    @property
    @abstractmethod
    def cleaners(self):
        pass


class Clean(ABC):
    @abstractmethod
    def clean(self, data):
        pass


class Serializable(ABC):
    """An interface for objects that use a DRF Serializer."""

    @property
    @abstractmethod
    def serializer_class(self):
        pass


class Updatable(ABC):
    """An interface for objects that can fetch an existing instance to update."""

    @abstractmethod
    def get_instance(self):
        pass


# ------------------------------------------------------------------
# 2. HIERARCHY 1: Model Builders
#    (Purpose: Create/Update DB Models & return their serialized data)
# ------------------------------------------------------------------


class ModelBuilder(Buildable, Cleanable, Serializable, ABC):
    """
    Base class for builders that create/update models using the Template Method Pattern.
    Its 'build' contract ALWAYS returns a serialized model dictionary.
    """

    def build(self):
        """Defines the algorithm for the model building process."""
        cleaned_data = self.clean()
        instance = self.perform_build(cleaned_data)
        return self.serializer_class(instance).data

    @abstractmethod
    def perform_build(self, data):
        """The specific create/update action to be implemented by subclasses."""
        pass

    def clean(self):
        """Applies all cleaner strategies to the data."""
        data = self.data
        for cleaner_class in self.cleaners:
            data = cleaner_class().clean(data)
        return data


class SessionModelBuilder(ModelBuilder, ABC):
    """A ModelBuilder that sources its data from and manages a Django session."""

    def __init__(self, request):
        self.data = request.session.get(self.name, {})
        request.session[self.name] = self.data
        self.session = request.session

    def decouple(self):
        if self.session and self.name in self.session:
            del self.session[self.name]

    def build(self):
        result = super().build()
        self.decouple()  # Decouple from session after a successful build
        return result


class CreateModelBuilder(SessionModelBuilder, ABC):
    """A SessionModelBuilder that specifically creates new model instances."""

    def perform_build(self, data):
        return self.serializer_class().create(data)


class UpdateModelBuilder(SessionModelBuilder, Updatable, ABC):
    """A SessionModelBuilder that specifically updates existing model instances."""

    def perform_build(self, data):
        instance = self.get_instance()
        return self.serializer_class().update(instance, data)


# --- Concrete Cleaner Strategy ---


class UserPasswordCleaner(Clean):
    """A strategy for cleaning and hashing password data."""

    def clean(self, data):
        # This cleaner is now self-contained and reusable.
        cleaned_data = {k: v for k, v in data.items() if k != "password_repeat"}
        if "password" in cleaned_data:
            cleaned_data["password"] = make_password(cleaned_data["password"])
        return cleaned_data


# --- Concrete Model Builders ---


class UserBuilder(CreateModelBuilder):
    name = "UserBuilder"
    serializer_class = UserSerializer
    cleaners = [UserPasswordCleaner]


class PasswordResetBuilder(UpdateModelBuilder):
    name = "PasswordResetBuilder"
    serializer_class = UserSerializer
    cleaners = [UserPasswordCleaner]

    def get_instance(self):
        return CustomUser.objects.get(email=self.data["email"])


# ------------------------------------------------------------------
# 3. HIERARCHY 2: API Response Builders
#    (Purpose: Construct a custom JSON response, NOT a model)
# ------------------------------------------------------------------


class APIResponseBuilder(Buildable, ABC):
    """
    Base class for builders that create custom API responses.
    Its 'build' contract can return ANY dictionary structure.
    LSP FIXED: This builder has a different parent and contract than ModelBuilder.
    """

    def __init__(self, data):
        self.data = data


class LoginBuilder(APIResponseBuilder):
    """A builder specifically for creating a JWT token response."""

    def build(self):
        user = CustomUser.objects.get(email=self.data["email"])
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Token expiration and storage logic...
        refresh_exp = datetime.datetime.fromtimestamp(
            refresh["exp"], tz=datetime.timezone.utc
        )
        access_exp = datetime.datetime.fromtimestamp(
            access["exp"], tz=datetime.timezone.utc
        )
        seconds_until_refresh_exp = int((refresh_exp - timezone.now()).total_seconds())
        seconds_until_access_exp = int((access_exp - timezone.now()).total_seconds())

        conn = get_redis_connection("default")
        conn.set(f"refresh_token:{str(refresh)}", 1, ex=seconds_until_refresh_exp)
        conn.set(f"access_token:{str(access)}", 1, ex=seconds_until_access_exp)

        # Return the custom token payload
        return {
            "refresh": str(refresh),
            "access": str(access),
            "email": self.data["email"],
        }


# ------------------------------------------------------------------
# 4. HIERARCHY 3: Service Input Builders
# ------------------------------------------------------------------


class ServiceInputBuilder(Buildable, ABC):
    """
    Base class for builders that simply extract and format input data for a service.
    Its 'build' contract returns a dictionary of required inputs.
    """

    def __init__(self, request):
        self.data = request.data

    def build(self):
        """Default implementation simply passes data through."""
        return self.data


class LogoutBuilder(ServiceInputBuilder):
    """A builder that extracts the refresh token for the LogoutService."""

    def build(self):
        return {
            "refresh": self.data.get("refresh")
        }


class TokenRefreshBuilder(ServiceInputBuilder):
    """A builder that extracts the refresh token for the TokenRefreshService."""

    def build(self):
        print('token refersh', self.data.get('refresh'))
        return {
            "refresh": self.data.get("refresh")
        }
