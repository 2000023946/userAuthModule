import logging
from abc import ABC, abstractmethod
from rest_framework import status

logger = logging.getLogger(__name__)


# --- Logger Strategies (No changes needed) ---


class AbstractLogger(ABC):
    @abstractmethod
    def log(self, msg):
        pass


class InfoLogger(AbstractLogger):
    def log(self, msg):
        logger.info(msg)


class WarningsLogger(AbstractLogger):
    def log(self, msg):
        logger.warning(msg)


class ErrorLogger(AbstractLogger):
    def log(self, msg):
        logger.error(msg)


# --- Abstract Contract for Message Formatting ---


class Loggable(ABC):
    @abstractmethod
    def _format_success_message(self, data):
        pass

    @abstractmethod
    def _format_failure_message(self, data):
        pass


# --- Template Method Pattern: The Abstract Orchestrator ---


class BaseEventLoggerFactory(Loggable):
    # Map status codes to the correct logger strategy
    _LOG_LEVEL_MAP = {
        status.HTTP_201_CREATED: InfoLogger,
        status.HTTP_200_OK: InfoLogger,
        status.HTTP_400_BAD_REQUEST: WarningsLogger,
        status.HTTP_401_UNAUTHORIZED: WarningsLogger,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorLogger,
    }

    def __init__(self):
        # Map status codes to the message-formatting methods to be implemented by subclasses
        self._MESSAGE_FORMAT_MAP = {
            status.HTTP_200_OK: self._format_success_message,
            status.HTTP_201_CREATED: self._format_success_message,
            status.HTTP_400_BAD_REQUEST: self._format_failure_message,
            status.HTTP_401_UNAUTHORIZED: self._format_failure_message,
        }

    def log(self, status_code, data):
        """The template method that orchestrates the logging process."""
        logger_class = self._LOG_LEVEL_MAP.get(status_code)
        message_formatter = self._MESSAGE_FORMAT_MAP.get(status_code)

        if logger_class and message_formatter:
            message = message_formatter(data)
            logger_instance = logger_class()
            logger_instance.log(message)


# --- Concrete Implementation for Login Events ---


class LoginLogger(BaseEventLoggerFactory):
    """Implements the message formatting for login-specific events."""

    def _format_success_message(self, data):
        return f"Login success for user '{data.get('email', 'N/A')}'. IP: {data.get('IP', 'N/A')}"

    def _format_failure_message(self, data):
        return f"Login failure for user '{data.get('email', 'N/A')}'. Reason: {data.get('error', 'Invalid credentials')}. IP: {data.get('IP', 'N/A')}"


class RegisterLogger(BaseEventLoggerFactory):
    """Implements the message formatting for registration-specific events."""

    def _format_success_message(self, data):
        # The 'create' key holds user data on successful registration
        user_data = data.get('create', {})
        return f"Registration success for user '{user_data.get('email', 'N/A')}'. IP: {data.get('IP', 'N/A')}"

    def _format_failure_message(self, data):
        return f"Registration failure. Reason: {data.get('errors', 'Validation failed')}. IP: {data.get('IP', 'N/A')}"


class PasswordResetLogger(BaseEventLoggerFactory):
    """Implements the message formatting for password reset events."""

    def _format_success_message(self, data):
        return f"Password reset initiated for '{data.get('message', 'N/A')}'. IP: {data.get('IP', 'N/A')}"

    def _format_failure_message(self, data):
        return f"Password Reset failed. Reason: {data.get('error', 'Unknown')}. IP: {data.get('IP', 'N/A')}"


class LogoutLogger(BaseEventLoggerFactory):
    """Implements message formatting for logout events."""

    def _format_success_message(self, data):
        # We don't have user info here, but we can log the action
        return f"Logout successful. IP: {data.get('IP', 'N/A')}"

    def _format_failure_message(self, data):
        return f"Logout failed. Reason: {data.get('error', 'Unknown')}. IP: {data.get('IP', 'N/A')}"


class TokenRefreshLogger(BaseEventLoggerFactory):
    """Implements message formatting for token refresh events."""

    def _format_success_message(self, data):
        # We can decode the new access token to get user info if needed
        return f"Token refresh successful. IP: {data.get('IP', 'N/A')}"

    def _format_failure_message(self, data):
        return f"Token refresh failed. Reason: {data.get('detail', 'Unknown')}. IP: {data.get('IP', 'N/A')}"
