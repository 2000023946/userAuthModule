from abc import ABC, abstractmethod
from rest_framework import status
from opentelemetry.trace import get_current_span

from UserAuthModule.settings import logger, ENVIRONMENT


# -----------------------------
# Logger Strategies
# -----------------------------
class AbstractLogger(ABC):
    @abstractmethod
    def log(self, msg, extra=None):
        pass


class InfoLogger(AbstractLogger):
    def log(self, msg, extra=None):
        logger.info(msg, extra=extra)


class WarningsLogger(AbstractLogger):
    def log(self, msg, extra=None):
        logger.warning(msg, extra=extra)


class ErrorLogger(AbstractLogger):
    def log(self, msg, extra=None):
        logger.error(msg, extra=extra)


# -----------------------------
# Abstract Loggable
# -----------------------------
class Loggable(ABC):
    @abstractmethod
    def _format_success_message(self, data):
        pass

    @abstractmethod
    def _format_failure_message(self, data):
        pass


# -----------------------------
# BaseEventLoggerFactory with Observability
# -----------------------------
class BaseEventLoggerFactory(Loggable):
    _LOG_LEVEL_MAP = {
        status.HTTP_201_CREATED: InfoLogger,
        status.HTTP_200_OK: InfoLogger,
        status.HTTP_400_BAD_REQUEST: WarningsLogger,
        status.HTTP_401_UNAUTHORIZED: WarningsLogger,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorLogger,
    }

    def __init__(self):
        self._MESSAGE_FORMAT_MAP = {
            status.HTTP_200_OK: self._format_success_message,
            status.HTTP_201_CREATED: self._format_success_message,
            status.HTTP_400_BAD_REQUEST: self._format_failure_message,
            status.HTTP_401_UNAUTHORIZED: self._format_failure_message,
            status.HTTP_500_INTERNAL_SERVER_ERROR: self._format_failure_message,
        }

    def log(self, status_code, data):
        logger_class = self._LOG_LEVEL_MAP.get(status_code)
        message_formatter = self._MESSAGE_FORMAT_MAP.get(status_code)

        if logger_class and message_formatter:
            message = message_formatter(data)
            logger_instance = logger_class()

            span = get_current_span()
            trace_id = span.get_span_context().trace_id if span else None

            # Include structured metadata for observability
            extra = {
                "request_id": data.get("request_id"),
                "user_id": data.get("user_id"),
                "user_email": data.get("email") or data.get("create", {}).get("email"),
                "ip": data.get("IP"),
                "trace_id": trace_id,
                "env": ENVIRONMENT,
            }
            logger_instance.log(message, extra=extra)


# --- Concrete Event Loggers with Observability ---


class LoginLogger(BaseEventLoggerFactory):
    def _format_success_message(self, data):
        return "Login success for user '{}'".format(data.get("email", "N/A"))

    def _format_failure_message(self, data):
        return "Login failure for user '{}'. Reason: {}".format(
            data.get("email", "N/A"), data.get("error", "Invalid credentials")
        )


class RegisterLogger(BaseEventLoggerFactory):
    def _format_success_message(self, data):
        user_data = data.get("create", {})
        return "Registration success for user '{}'".format(
            user_data.get("email", "N/A")
        )

    def _format_failure_message(self, data):
        return "Registration failure. Reason: {}".format(
            data.get("errors", "Validation failed")
        )


class PasswordResetLogger(BaseEventLoggerFactory):
    def _format_success_message(self, data):
        return "Password reset initiated for '{}'".format(data.get("message", "N/A"))

    def _format_failure_message(self, data):
        return "Password reset failed. Reason: {}".format(data.get("error", "Unknown"))


class LogoutLogger(BaseEventLoggerFactory):
    def _format_success_message(self, data):
        return "Logout successful."

    def _format_failure_message(self, data):
        return "Logout failed. Reason: {}".format(data.get("error", "Unknown"))


class TokenRefreshLogger(BaseEventLoggerFactory):
    def _format_success_message(self, data):
        return "Token refresh successful."

    def _format_failure_message(self, data):
        return "Token refresh failed. Reason: {}".format(data.get("detail", "Unknown"))


class TokenValidationLogger(BaseEventLoggerFactory):
    def _format_success_message(self, data):
        return "Token validation successful."

    def _format_failure_message(self, data):
        return "Token validation failed. Reason: {}".format(
            data.get("detail", "Unknown")
        )
