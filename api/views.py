# api/views.py

from abc import ABC, abstractmethod

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
# --- FIX: Added necessary imports for token refresh logic ---
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import CustomUser

# Local Imports: Import the new SOLID service and builder classes
from .builder import (
    UserBuilder,
    PasswordResetBuilder,
    LoginBuilder,
    APIResponseBuilder,
    ModelBuilder,
)
from .services import (
    StatefulRegistrationService,
    StatelessRegistrationService,
    RegistrationFactory,
    PasswordResetFactory,
    LoginFactory,
    ThirdPartyRegistrationFactory,
    ThirdPartyLoginFactory,
    ThirdPartyStrategySingleton,
    ServiceStateFactory,
)

# ------------------------------------------------------------------
# BASE AUTHENTICATION VIEW
# ------------------------------------------------------------------


class BaseAuthView(APIView, ABC):
    """
    An abstract base view that orchestrates the service, builder, and factory.
    Subclasses must define which concrete implementations to use.
    """

    permission_classes = [AllowAny]

    # --- Abstract properties for subclasses to implement ---

    @property
    @abstractmethod
    def service_class(self) -> type[StatefulRegistrationService | StatelessRegistrationService]:
        """Specifies the service class to use (e.g., Stateful or Stateless)."""
        pass

    @property
    @abstractmethod
    def builder_class(self) -> type[ModelBuilder | APIResponseBuilder]:
        """Specifies the builder class to use."""
        pass

    @property
    @abstractmethod
    def factory_class(self) -> type[ServiceStateFactory]:
        """Specifies the state machine factory to use."""
        pass

    # --- Core Logic ---

    def post(self, request, *args, **kwargs):
        """
        Handles the POST request by initializing and executing the appropriate service.
        The 'kwargs' can contain pre-processed data, like from a third-party login.
        """
        service = self.get_service(request, **kwargs)
        builder = self.get_builder(request, **kwargs)
        state_machine = self.factory_class().build()

        result = service.execute(builder, state_machine)

        return Response(result, status=self.get_status_code(result))

    def get_service(self, request, **kwargs):
        """Initializes the correct service with either the request or data."""
        if "data" in kwargs:
            return self.service_class(kwargs["data"])
        return self.service_class(request)

    def get_builder(self, request, **kwargs):
        """Initializes the correct builder with either the request or data."""
        # --- FIX: Use issubclass() for a more robust type check ---
        if issubclass(self.builder_class, APIResponseBuilder):
            data = kwargs.get("data", request.data)
            return self.builder_class(data)
        return self.builder_class(request)

    def get_status_code(self, result: dict) -> int:
        """Determines the appropriate HTTP status code from the service result."""
        if "create" in result:
            return status.HTTP_201_CREATED
        if "errors" in result:
            return status.HTTP_400_BAD_REQUEST
        return status.HTTP_200_OK


# ------------------------------------------------------------------
# CONCRETE AUTHENTICATION VIEWS
# ------------------------------------------------------------------


class RegisterView(BaseAuthView):
    service_class = StatefulRegistrationService
    builder_class = UserBuilder
    factory_class = RegistrationFactory


class LoginView(BaseAuthView):
    service_class = StatefulRegistrationService
    builder_class = LoginBuilder
    factory_class = LoginFactory


class PasswordResetView(BaseAuthView):
    service_class = StatefulRegistrationService
    builder_class = PasswordResetBuilder
    factory_class = PasswordResetFactory


# ------------------------------------------------------------------
# THIRD-PARTY AUTHENTICATION VIEWS
# ------------------------------------------------------------------


class ThirdPartyAuthView(BaseAuthView):
    """Base view for handling third-party authentication."""

    service_class = StatelessRegistrationService

    def post(self, request, *args, **kwargs):
        """
        Overrides post to first get user info from the third party,
        then calls the parent's post method with that info.
        """
        provider = request.data.get("provider")
        token = request.data.get("token")

        if not provider or not token:
            return Response(
                {"errors": "Provider and token are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_info = ThirdPartyStrategySingleton.get_user_info(provider, token)
            return super().post(request, data=user_info)
        except (ValueError, KeyError) as e:
            return Response({"errors": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ThirdPartyRegisterView(ThirdPartyAuthView):
    builder_class = UserBuilder
    factory_class = ThirdPartyRegistrationFactory


class ThirdPartyLoginView(ThirdPartyAuthView):
    builder_class = LoginBuilder
    factory_class = ThirdPartyLoginFactory


# ------------------------------------------------------------------
# OTHER VIEWS
# ------------------------------------------------------------------


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": f"Hello {request.user.email}"})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            conn = get_redis_connection("default")
            ttl = conn.ttl(f"refresh_token:{refresh_token}")
            if ttl > 0:
                # This key is now consistent with the fixed TokenValidationView
                conn.set(f"blacklisted_token:{refresh_token}", "true", ex=ttl)

            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# --- FIX: This entire view has been rewritten for correctness and security ---
class TokenValidationView(APIView):
    """
    This view acts as a token refresh endpoint.
    It validates a refresh token and returns a new pair of access and refresh tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token_str = request.data.get("refresh")
        if not refresh_token_str:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conn = get_redis_connection("default")

        # 1. Check if the token has been explicitly blacklisted (e.g., by logout)
        if conn.get(f"blacklisted_token:{refresh_token_str}"):
            return Response(
                {"detail": "Token is blacklisted."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 2. Check if the token is in our cache of active refresh tokens
        if not conn.get(f"refresh_token:{refresh_token_str}"):
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # 3. Decode the token to get the user and perform token rotation
            refresh_token = RefreshToken(refresh_token_str)
            user_id = refresh_token.get("user_id")
            user = CustomUser.objects.get(id=user_id)

            # 4. Blacklist the OLD refresh token to prevent reuse
            ttl = conn.ttl(f"refresh_token:{refresh_token_str}")
            if ttl > 0:
                conn.set(f"blacklisted_token:{refresh_token_str}", "true", ex=ttl)

            # 5. Use the LoginBuilder to generate a new token pair for the user
            new_tokens = LoginBuilder({"email": user.email}).build()

            return Response(new_tokens, status=status.HTTP_200_OK)

        except (TokenError, CustomUser.DoesNotExist):
            return Response(
                {"detail": "Token is invalid or user not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )