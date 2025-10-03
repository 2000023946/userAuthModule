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
    APIResponseBuilder,
    LogoutBuilder,
    TokenRefreshBuilder,
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
    LogoutService,
    TokenRefreshService,
)
from .loggers import (
    LoginLogger,
    RegisterLogger,
    PasswordResetLogger,
    LogoutLogger,
    TokenRefreshLogger,
)


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

    def get_service(self, request, **kwargs):
        if "data" in kwargs:
            return self.service_class(kwargs["data"])
        return self.service_class(request)

    def get_builder(self, request, **kwargs):
        """Initializes the correct builder with either the request or data."""
        if issubclass(self.builder_class, APIResponseBuilder):
            data = kwargs.get("data", request.data)
            return self.builder_class(data)
        return self.builder_class(request)

    def get_status_code(self, result: dict) -> int:
        if "create" in result:
            return status.HTTP_201_CREATED
        if "errors" in result:
            return status.HTTP_400_BAD_REQUEST
        return status.HTTP_200_OK

    def _get_logging_data(self, result):
        ip = self.request.META.get("REMOTE_ADDR")
        log_data = result.copy()
        log_data["IP"] = ip
        return log_data


class StatefulAuthView(BaseAuthView):
    """
    A specialized base view for stateful operations that require a state machine.
    """

    @property
    @abstractmethod
    def factory_class(self):
        """Specifies the state machine factory to use."""
        pass

    def post(self, request, *args, **kwargs):
        service = self.get_service(request, **kwargs)
        builder = self.get_builder(request, **kwargs)
        state_machine = self.factory_class().build()

        result = service.execute(builder, state_machine)
        status_code = self.get_status_code(result)
        log_data = self._get_logging_data(result)

        logger_instance = self.logger()
        logger_instance.log(status_code, log_data)

        return Response(result, status=status_code)


class StatelessAuthView(BaseAuthView):
    """
    A specialized base view for stateless operations that do not use a state machine.
    """

    def post(self, request, *args, **kwargs):
        service = self.get_service(request, **kwargs)
        builder = self.get_builder(request, **kwargs)

        result = service.execute(builder)
        status_code = self.get_status_code(result)
        log_data = self._get_logging_data(result)

        logger_instance = self.logger()
        logger_instance.log(status_code, log_data)

        return Response(result, status=status_code)


# ------------------------------------------------------------------
# CONCRETE AUTHENTICATION VIEWS
# ------------------------------------------------------------------


class RegisterView(StatefulAuthView):
    service_class = StatefulRegistrationService
    builder_class = UserBuilder
    factory_class = RegistrationFactory
    logger = RegisterLogger


class LoginView(StatefulAuthView):
    service_class = StatefulRegistrationService
    builder_class = LoginBuilder
    factory_class = LoginFactory
    logger = LoginLogger


class PasswordResetView(StatefulAuthView):
    service_class = StatefulRegistrationService
    builder_class = PasswordResetBuilder
    factory_class = PasswordResetFactory
    logger = PasswordResetLogger


# ------------------------------------------------------------------
# THIRD-PARTY AUTHENTICATION VIEWS
# ------------------------------------------------------------------


class ThirdPartyAuthView(StatefulAuthView):
    """Base view for handling third-party authentication."""
    service_class = StatelessRegistrationService

    def post(self, request, *args, **kwargs):
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
    logger = RegisterLogger


class ThirdPartyLoginView(ThirdPartyAuthView):
    builder_class = LoginBuilder
    factory_class = ThirdPartyLoginFactory
    logger = LoginLogger


# ------------------------------------------------------------------
# OTHER VIEWS
# ------------------------------------------------------------------


class LogoutView(StatelessAuthView):
    permission_classes = [IsAuthenticated]
    service_class = LogoutService
    builder_class = LogoutBuilder
    logger = LogoutLogger

    def get_status_code(self, result: dict) -> int:
        if "error" in result:
            return status.HTTP_400_BAD_REQUEST
        return status.HTTP_205_RESET_CONTENT


class TokenRefreshView(StatelessAuthView):
    permission_classes = [AllowAny]
    service_class = TokenRefreshService
    builder_class = TokenRefreshBuilder
    logger = TokenRefreshLogger

    def get_status_code(self, result: dict) -> int:
        if "detail" in result or "error" in result:
            return status.HTTP_401_UNAUTHORIZED
        return status.HTTP_200_OK
