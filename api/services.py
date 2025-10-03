import requests  # type: ignore
from abc import ABC, abstractmethod
from django_redis import get_redis_connection
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .builder import LoginBuilder
from .validators import (
    DefaultValidator,
    PasswordRepeatValidator,
    PasswordValidator,
    EmailValidator,
    EmailResetValidator,
    UsernameValidator,
    UserRegistrationValidator,
    PasswordResetValidator,
)


# ------------------------------------------------------------------
# SERVICE INTERFACE AND IMPLEMENTATIONS
# ------------------------------------------------------------------


class Servicable(ABC):
    """A single, unified interface for all service classes."""

    @abstractmethod
    def execute(self, builder, state_machine=None):
        pass


class LogoutService(Servicable):
    def __init__(self, request):
        self.request = request

    def execute(self, builder, state_machine=None):
        data = builder.build()
        refresh_token = data.get("refresh")

        if not refresh_token:
            return {"error": "Refresh token is required."}

        try:
            conn = get_redis_connection("default")
            ttl = conn.ttl(f"refresh_token:{refresh_token}")
            if ttl > 0:
                conn.set(f"blacklisted_token:{refresh_token}", "true", ex=ttl)
            return {"message": "Logout successful. Tokens invalidated."}
        except Exception:  # noqa: F841
            return {"errors": "An unexpected error occurred during logout."}


class TokenRefreshService(Servicable):
    def __init__(self, request):
        self.request = request

    def execute(self, builder, state_machine=None):
        data = builder.build()
        refresh_token_str = data.get("refresh")

        if not refresh_token_str:
            return {"detail": "Refresh token is required."}

        conn = get_redis_connection("default")
        if conn.get(f"blacklisted_token:{refresh_token_str}"):
            return {"detail": "Token is blacklisted."}
        if not conn.get(f"refresh_token:{refresh_token_str}"):
            return {"detail": "Invalid or expired refresh token."}

        try:
            refresh_token = RefreshToken(refresh_token_str)
            user_id = refresh_token.get("user_id")
            user = CustomUser.objects.get(id=user_id)

            ttl = conn.ttl(f"refresh_token:{refresh_token_str}")
            if ttl > 0:
                conn.set(f"blacklisted_token:{refresh_token_str}", "true", ex=ttl)

            new_tokens = LoginBuilder({"email": user.email}).build()
            return new_tokens
        except (TokenError, CustomUser.DoesNotExist):
            return {"detail": "Token is invalid or user not found."}
        except Exception:  # noqa: F841
            return {"errors": "An unexpected error occurred during token refresh."}


# ------------------------------------------------------------------
# BASE SERVICE (Template Method Pattern)
# ------------------------------------------------------------------


class RegistrationService(Servicable):
    """
    Abstract base class defining the template for processing a state machine.
    """

    def execute(self, builder, initial_state):
        """Template method defining the skeleton of execution."""
        self._initialize(builder, initial_state)

        for key, value in self._get_data().items():
            step_successful = self._process_step(key, value)
            if not step_successful:
                break

            self._on_step_success()

            if self._is_finished():
                validation_successful = self._validate_finish_step(key, value)
                if validation_successful:
                    self.result = {"create": self.builder.build()}
                break

        return self._get_result()

    def _initialize(self, builder, initial_state):
        """Hook for initializing state, builder, and data before execution."""
        self.builder = builder
        self.state = initial_state
        self.errors = {}
        self.result = {}

    def _process_step(self, key, value):
        """Processes a single step/state in the machine."""
        try:
            self.state = self.state.handle(key, value, self.builder)
            return True
        except ValueError as e:
            self.errors[self.state.name] = str(e)
            return False

    def _on_step_success(self):
        """Hook for actions to perform after a successful step."""
        pass

    def _is_finished(self):
        """Checks if the state machine has reached its terminal state."""
        return self.state.is_finish()

    def _validate_finish_step(self, key, value):
        """Performs a final validation check on the terminal state."""
        return self._process_step(key, value)

    def _get_result(self):
        """Formats and returns the final result of the execution."""
        if self.result:
            return self.result
        if self.errors:
            return {"errors": self.errors}
        return {"message": f"Continue at state {self.state.name}"}

    @abstractmethod
    def _get_data(self):
        """Abstract method for subclasses to provide the input data."""
        pass


# ------------------------------------------------------------------
# CONCRETE IMPLEMENTATIONS
# ------------------------------------------------------------------


class StatefulRegistrationService(RegistrationService):
    """Service for multi-request workflows using sessions."""

    def __init__(self, request):
        self.request = request
        self.session = getattr(request, "session", None)

    def _get_data(self):
        return getattr(self.request, "data", {})

    def _initialize(self, builder, initial_state):
        super()._initialize(builder, initial_state)
        if self.session and "state" in self.session:
            state_to_start = self.session["state"]
            current = initial_state
            while current and not current.__eq__(state_to_start):
                current = current.next
            self.state = current or initial_state

    def _on_step_success(self):
        if self.session:
            self.session["state"] = self.state.name


class StatelessRegistrationService(RegistrationService):
    """Service for single-shot workflows with all data provided at once."""

    def __init__(self, data):
        self.data = data

    def _get_data(self):
        return self.data


# ------------------------------------------------------------------
# FACTORIES
# ------------------------------------------------------------------


class ServiceStateFactory(ABC):
    @abstractmethod
    def build(self):
        """Return a configured state chain."""
        pass


class RegistrationFactory(ServiceStateFactory):
    def build(self):
        return (
            UsernameState()
            .then_handle(EmailState())
            .then_handle(PasswordState())
            .then_handle(PasswordRepeatState())
            .then_handle(CompleteRegistrationState())
        )


class PasswordResetFactory(ServiceStateFactory):
    def build(self):
        return (
            EmailExistsState()
            .then_handle(PasswordState())
            .then_handle(PasswordRepeatState())
            .then_handle(CompletePasswordResetState())
        )


class ThirdPartyRegistrationFactory(ServiceStateFactory):
    def build(self):
        return EmailState().then_handle(CompleteState())


class LoginFactory(ServiceStateFactory):
    def build(self):
        return (
            EmailExistsState()
            .then_handle(PasswordState())
            .then_handle(CompleteLoginState())
        )


class ThirdPartyLoginFactory(ServiceStateFactory):
    def build(self):
        return EmailExistsState().then_handle(CompleteState())


# ------------------------------------------------------------------
# STATE MACHINE
# ------------------------------------------------------------------


class State(ABC):
    validator = DefaultValidator()

    def __init__(self):
        self.next = None

    def handle(self, key, value, builder):
        if self.validator.validate(value, builder.data):
            builder.register(key, value)
            return self.next
        return self

    def then_handle(self, next_state):
        tail = self
        while tail.next is not None:
            tail = tail.next
        tail.next = next_state
        return self

    def is_finish(self):
        return False

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return isinstance(other, State) and other.name == self.name


class PasswordRepeatState(State):
    validator = PasswordRepeatValidator()
    name = "PasswordRepeat"


class PasswordState(State):
    validator = PasswordValidator()
    name = "Password"


class EmailState(State):
    validator = EmailValidator()
    name = "Email"


class EmailExistsState(State):
    validator = EmailResetValidator()
    name = "Email"


class UsernameState(State):
    validator = UsernameValidator()
    name = "Username"


class CompleteState(State):
    def is_finish(self):
        return True


class CompleteRegistrationState(CompleteState):
    name = "CompleteRegistration"
    validator = UserRegistrationValidator()


class CompletePasswordResetState(CompleteState):
    name = "CompletePasswordReset"
    validator = PasswordResetValidator()


class CompleteLoginState(CompleteState):
    name = "CompleteLogin"


# ------------------------------------------------------------------
# THIRD-PARTY STRATEGY
# ------------------------------------------------------------------


class ThirdPartyStrategy(ABC):
    @abstractmethod
    def get_user_info(self, token):
        pass


class GoogleStrategy(ThirdPartyStrategy):
    def get_user_info(self, token):
        google_verify_url = "https://oauth2.googleapis.com/tokeninfo"
        resp = requests.get(google_verify_url, params={"id_token": token})
        if resp.status_code != 200:
            raise ValueError("Invalid Google token")

        payload = resp.json()
        return {
            "email": payload["email"],
            "username": payload.get("name", ""),
        }


class ThirdPartyStrategySingleton:
    strategies = {"google": GoogleStrategy}

    @classmethod
    def get_user_info(cls, provider, token):
        return cls.strategies[provider]().get_user_info(token)
