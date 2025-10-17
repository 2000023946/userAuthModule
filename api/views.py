from abc import ABC, abstractmethod

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Local Imports
from .builder import (
    UserBuilder,
    PasswordResetBuilder,
    LoginBuilder,
    LogoutBuilder,
    TokenRefreshBuilder,
    OAuthUserInfoBuilder,
    ValidationTokenBuilder,
)
from .services import (
    RedisAuthService,
    OneShotAuthService,
)
from .loggers import (
    LoginLogger,
    RegisterLogger,
    PasswordResetLogger,
    LogoutLogger,
    TokenRefreshLogger,
)
from .states import (
    RegistrationFactory,
    PasswordResetFactory,
    LoginFactory,
    ThirdPartyRegistrationFactory,
    ThirdPartyLoginFactory,
    FullTokenFactory,
    RefreshTokenFactory,
    OAuthTokenFactory,
)
from api.metrics import (
    RegistrationMetrics,
    LoginMetrics,
    LogoutMetrics,
    PasswordResetRequestMetrics,
    ThirdPartyLoginMetrics,
    ThirdPartyRegisterMetrics,
    TokenRefreshMetrics,
    track_metrics,
)
from .tracers import trace


# ------------------------------------------------------------------
# BASE AUTHENTICATION VIEWS
# ------------------------------------------------------------------


class BaseAuthView(APIView, ABC):
    """
    The root abstract view. Defines the common interface for services,
    builders, and loggers, but leaves the execution logic to subclasses.
    """

    permission_classes = [AllowAny]

    @property
    @abstractmethod
    def service_class(self):
        pass

    @property
    @abstractmethod
    def builder_class(self):
        pass

    @property
    @abstractmethod
    def logger(self):
        pass

    @abstractmethod
    def post(self, request, *args, **kwargs):
        """Execution logic is deferred to subclasses."""
        pass

    @property
    @abstractmethod
    def factory_class(self):
        """Specifies the state machine factory to use."""
        pass

    @property
    @abstractmethod
    def metrics(self):
        """Specifies the metrics to use."""
        pass

    @abstractmethod
    def get_data(self, data):
        """Method used for strategy on how each view passes in the data"""


class AuthView(BaseAuthView):
    """
    A specialized base view for stateful operations that require a state machine.
    """

    @trace(lambda self: f"{self.__class__.__name__}_post")
    @track_metrics(lambda self: self.metrics)
    def post(self, request, *args, **kwargs):
        data = self.get_data()
        if not data or "errors" in data:
            return Response(
                data if data else {"errors": "Data cannot be empty"},
                status=self.get_status_code(data),
            )

        builder = self.builder_class()
        service = self.service_class()
        state_machine = self.factory_class().build()
        logger = self.logger()

        result = service.execute(self.get_data(), builder, state_machine)
        status_code = self.get_status_code(result)
        log_data = self._get_logging_data(result)
        logger.log(status_code, log_data)

        print("res", result)

        return Response(result, status=status_code)

    def get_data(self):
        return self.request.data

    def get_status_code(self, result: dict) -> int:
        if "create" in result:
            return status.HTTP_201_CREATED
        if "errors" in result or not result:
            return status.HTTP_400_BAD_REQUEST
        return status.HTTP_200_OK

    def _get_logging_data(self, result):
        ip = self.request.META.get("REMOTE_ADDR")
        log_data = result.copy()
        log_data["IP"] = ip
        return log_data


# ------------------------------------------------------------------
# CONCRETE AUTHENTICATION VIEWS
# ------------------------------------------------------------------


class RegisterView(AuthView):
    service_class = RedisAuthService
    builder_class = UserBuilder
    factory_class = RegistrationFactory
    logger = RegisterLogger
    metrics = RegistrationMetrics()


class LoginView(AuthView):
    service_class = RedisAuthService
    builder_class = LoginBuilder
    factory_class = LoginFactory
    logger = LoginLogger
    metrics = LoginMetrics()


class PasswordResetView(AuthView):
    service_class = RedisAuthService
    builder_class = PasswordResetBuilder
    factory_class = PasswordResetFactory
    logger = PasswordResetLogger
    metrics = PasswordResetRequestMetrics()


# ------------------------------------------------------------------
# THIRD-PARTY AUTHENTICATION VIEWS
# ------------------------------------------------------------------


class ThirdPartyAuthView(AuthView):
    """Base view for handling third-party authentication."""

    service_class = OneShotAuthService

    def get_data(self):
        # Execute the custom logic here and return the processed data
        builder = OAuthUserInfoBuilder()
        state_machine = OAuthTokenFactory().build()
        service = self.service_class()

        result = service.execute(self.request.data, builder, state_machine)
        self.user_info = result
        print("user info", self.user_info)
        return result[list(result.keys())[0]]


class ThirdPartyRegisterView(ThirdPartyAuthView):
    builder_class = UserBuilder
    factory_class = ThirdPartyRegistrationFactory
    logger = RegisterLogger
    metrics = ThirdPartyRegisterMetrics()


class ThirdPartyLoginView(ThirdPartyAuthView):
    builder_class = LoginBuilder
    factory_class = ThirdPartyLoginFactory
    logger = LoginLogger
    metrics = ThirdPartyLoginMetrics()


# ------------------------------------------------------------------
# OTHER VIEWS
# ------------------------------------------------------------------


class LogoutView(AuthView):
    permission_classes = [IsAuthenticated]
    service_class = OneShotAuthService
    builder_class = LogoutBuilder
    logger = LogoutLogger
    factory_class = FullTokenFactory
    metrics = LogoutMetrics()

    def get_status_code(self, result: dict) -> int:
        if "errors" in result:
            return status.HTTP_400_BAD_REQUEST
        return status.HTTP_205_RESET_CONTENT


class ValidateTokenView(AuthView):
    permission_classes = [AllowAny]
    service_class = OneShotAuthService
    builder_class = ValidationTokenBuilder
    logger = ValidationTokenBuilder  # Reusing LoginLogger for simplicity
    factory_class = FullTokenFactory
    metrics = ValidationTokenBuilder  # No specific metrics for validation

    def get_status_code(self, result: dict) -> int:
        if "errors" in result:
            return status.HTTP_401_UNAUTHORIZED
        return status.HTTP_200_OK


class TokenRefreshView(AuthView):
    service_class = OneShotAuthService
    builder_class = TokenRefreshBuilder
    logger = TokenRefreshLogger
    factory_class = RefreshTokenFactory
    metrics = TokenRefreshMetrics()

    def get_status_code(self, result: dict) -> int:
        if "errors" in result:
            return status.HTTP_401_UNAUTHORIZED
        return status.HTTP_200_OK
