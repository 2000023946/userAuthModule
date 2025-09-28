import requests  # type: ignore
from abc import ABC, abstractmethod  # import before using

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


class RegistrationService:
    def get_data(self, data_object):
        # If data_object has a `session` attribute, use request.data
        if hasattr(data_object, "session"):
            return getattr(data_object, "data", {})  # DRF Request stores data in `.data`
        # If it's a dict-like object, just return it
        return data_object

    def execute(self, request, builder, state):
        """
        Processes the request data step by step through the state machine.
        Returns a dict with one of:
          {"create": created_object_data}
          {"errors": {state_name: error_msg}}
          {"message": "some message"}
        """
        state = self.get_starting_state(request, state)
        errors = {}

        for key, value in self.get_data(request).items():
            print(value, "2345value")
            try:
                state = state.handle(key, value, builder)
                self.save(request, state)
            except ValueError as e:
                errors[state.name] = str(e)
                break

            if state.is_finish():  # final overall validation
                try:
                    state.handle(key, value, builder)
                except ValueError as e:
                    errors[state.name] = str(e)
                    break
                # registration finished successfully
                created = builder.build()
                return {"create": created}

        if errors:
            return {"errors": errors}

        # if loop ends without finish/error, you can send intermediate message
        return {"message": f"Continue at state {state.name}"}

    def save(self, request, state):
        if hasattr(request, "session"):
            request.session["state"] = state.name

    def get_starting_state(self, request, state):
        if not hasattr(request, "session") or "state" not in request.session:
            return state
        state_to_start = request.session["state"]
        current = state
        while current and not current.__eq__(state_to_start):
            current = current.next
        return current or state


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


class State(ABC):
    validator = DefaultValidator()

    def __init__(self):
        self.next = None

    def handle(self, key, value, builder):
        # Pass both current data and accumulated data to validator
        if self.validator.validate(value, builder.data):
            builder.register(key, value)
            return self.next
        return self

    def then_handle(self, next_state):
        """
        Attach `next_state` at the end of the chain.
        Returns self (head of the chain) so we can chain safely.
        """
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
    strategies = {
        "google": GoogleStrategy,
    }

    @classmethod
    def get_user_info(cls, provider, token):
        return cls.strategies[provider]().get_user_info(token)
