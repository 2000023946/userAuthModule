# .utils import hash_token # Assuming this exists
from abc import ABC, abstractmethod

import jwt

from UserAuthModule import settings


# Import your validators here...
from .validators import (
    DefaultStateValidator,
    PasswordValidator,
    EmailValidator,
    EmailResetValidator,
    UsernameValidator,
    UserRegistrationValidator,
    PasswordResetValidator,
    TokenRefreshValidator,
    RefreshTokenValidator,
    AccessTokenValidator,
    ProviderValidator,
    OAuthTokenValidator,
)
from .utils import hash_token

# Import RefreshToken if it's defined elsewhere in your project
from rest_framework_simplejwt.tokens import RefreshToken
from .tracers import trace


# ------------------------------------------------------------------
# STATE FLOW VALIDATORS (NEW)
# ------------------------------------------------------------------


class StateFlowValidator(ABC):
    """An interface for state flow validation strategies."""

    @abstractmethod
    def validate(self, state_list):
        pass


class DefaultStateFlowValidator(StateFlowValidator):
    """Performs basic validation that should apply to ALL state flows."""

    def validate(self, state_list):
        if not (
            self._validate_has_complete_state(state_list)
            and self._validate_no_duplicate_names(state_list)
        ):
            return False
        return True

    def _validate_has_complete_state(self, state_list):
        if not state_list or not isinstance(state_list[-1], CompleteState):
            return False
        return True

    def _validate_no_duplicate_names(self, state_list):
        name_set = set()
        for state in state_list:
            if state.name in name_set:
                return False
            name_set.add(state.name)
        return True


class PasswordStateFlowValidator(DefaultStateFlowValidator):
    """
    Inherits the default validations and ADDS password-specific security rules.
    """

    def validate(self, state_list):
        if not super().validate(state_list):
            return False

        if not self._validate_password_is_final_input(state_list):
            return False

        return True

    def _validate_password_is_final_input(self, state_list):
        try:
            first_password_index = next(
                i
                for i, s in enumerate(state_list)
                if isinstance(s, PasswordSensitiveState)
            )
            for i in range(first_password_index + 1, len(state_list)):
                subsequent_state = state_list[i]
                if not isinstance(
                    subsequent_state, (PasswordSensitiveState, CompleteState)
                ):
                    return False
            return True
        except StopIteration:
            return True


# ------------------------------------------------------------------
# FACTORIES
# ------------------------------------------------------------------


class InvalidStateFlowException(Exception):
    pass


class AbstractServiceStateFactory(ABC):
    @trace(lambda self: f"{self.__class__.__name__}_build")
    @abstractmethod
    def configure(self):
        pass


class ServiceStateFactory(AbstractServiceStateFactory, ABC):

    @property
    @abstractmethod
    def validator_classes(self) -> list[StateFlowValidator]:
        pass

    def build(self):
        start_state = self.configure()
        state_list = self._flatten_states(start_state)

        for validator_class in self.validator_classes:
            validator = validator_class()
            if not validator.validate(state_list):
                raise InvalidStateFlowException(
                    f"Invalid state flow in {self.__class__.__name__}"
                )

        return start_state

    def _flatten_states(self, start_state):
        states = []
        current = start_state
        while current:
            states.append(current)
            current = current.next
        return states


class RegistrationFactory(ServiceStateFactory):
    validator_classes = [PasswordStateFlowValidator]

    def configure(self):
        return (
            UsernameState()
            .then_handle(EmailState())
            .then_handle(PasswordState())
            .then_handle(PasswordRepeatState())
            .then_handle(CompleteRegistrationState())
        )


class PasswordResetFactory(ServiceStateFactory):
    validator_classes = [PasswordStateFlowValidator]

    def configure(self):
        return (
            EmailExistsState()
            .then_handle(PasswordState())
            .then_handle(PasswordRepeatState())
            .then_handle(CompletePasswordResetState())
        )


class ThirdPartyRegistrationFactory(ServiceStateFactory):
    validator_classes = [DefaultStateFlowValidator]

    def configure(self):
        return EmailState().then_handle(CompleteState())


class LoginFactory(ServiceStateFactory):
    validator_classes = [PasswordStateFlowValidator]

    def configure(self):
        return (
            EmailExistsState()
            .then_handle(PasswordState())
            .then_handle(CompleteLoginState())
        )


class ThirdPartyLoginFactory(ServiceStateFactory):
    validator_classes = [DefaultStateFlowValidator]

    def configure(self):
        return EmailExistsState().then_handle(CompleteState())


class FullTokenFactory(ServiceStateFactory):
    validator_classes = [DefaultStateFlowValidator]

    def configure(self):
        return (
            AccessState().then_handle(RefreshState()).then_handle(CompleteTokenState())
        )


class RefreshTokenFactory(ServiceStateFactory):
    validator_classes = [DefaultStateFlowValidator]

    def configure(self):
        return RefreshState().then_handle(CompleteTokenState())


class OAuthTokenFactory(ServiceStateFactory):
    validator_classes = [DefaultStateFlowValidator]

    def configure(self):
        return (
            ProviderState()
            .then_handle(OAuthTokenState())
            .then_handle(CompleteOAuthState())
        )


class Output(ABC):
    @abstractmethod
    def output(self, value):
        pass


class DefaultOutput(Output):
    def output(self, value):
        return value


class PasswordOutput(Output):
    def output(self, value):
        return hash_token(value)


class AccessOutput(Output):
    def output(self, value):
        return jwt.decode(value, settings.SECRET_KEY, algorithms=["HS256"])


class RefreshTokenOutput(Output):
    def output(self, value):
        return RefreshToken(value).payload


# ------------------------------------------------------------------
# STATE MACHINE
# ------------------------------------------------------------------


class State(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def getter_class(self):
        pass

    @property
    @abstractmethod
    def validator(self):
        pass

    @property
    @abstractmethod
    def is_finish(self):
        pass

    def get_data(self, value):
        return self.getter_class().output(value)


class DefaultState(State, ABC):
    validator = DefaultStateValidator()
    getter_class = DefaultOutput()

    def __init__(self):
        self.next = None

    def handle(self, value):
        if self.validator.validate(value):
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


class NonSensitiveState(DefaultState):
    getter_class = DefaultOutput
    name = "non sensitive data state"


class TokenState(DefaultState):
    getter_class = DefaultOutput
    name = "token data state"


class PasswordSensitiveState(DefaultState):
    getter_class = PasswordOutput
    name = "password senvsitive state"


class CompleteState(DefaultState):
    name = "complete state"
    getter_class = DefaultOutput

    # --- FIX WAS HERE ---
    # This now correctly returns a boolean value.
    def is_finish(self):
        return True


class PasswordRepeatState(PasswordSensitiveState):
    validator = PasswordValidator()
    name = "PasswordRepeat"
    getter_class = DefaultOutput


class PasswordState(PasswordSensitiveState):
    validator = PasswordValidator()
    name = "Password"


class EmailState(NonSensitiveState):
    validator = EmailValidator()
    name = "Email"


class EmailExistsState(NonSensitiveState):
    validator = EmailResetValidator()
    name = "Email"


class UsernameState(NonSensitiveState):
    validator = UsernameValidator()
    name = "Username"


class RefreshState(TokenState):
    validator = RefreshTokenValidator()
    getter_class = RefreshTokenOutput
    name = "refresh"


class AccessState(TokenState):
    validator = AccessTokenValidator()
    name = "access"


class ProviderState(NonSensitiveState):
    validator = ProviderValidator()
    name = "provider"


class OAuthTokenState(TokenState):
    validator = OAuthTokenValidator()
    name = "oauth"


class CompleteRegistrationState(CompleteState):
    name = "CompleteRegistration"
    validator = UserRegistrationValidator()


class CompletePasswordResetState(CompleteState):
    name = "CompletePasswordReset"
    validator = PasswordResetValidator()


class CompleteLoginState(CompleteState):
    name = "CompleteLogin"
    validator = DefaultStateValidator()  # Added to make concrete


class CompleteTokenState(CompleteState):
    name = "CompleteTokenState"
    validator = TokenRefreshValidator()


class CompleteOAuthState(CompleteState):
    name = "CompleteOAuthState"
    validator = DefaultStateValidator()
