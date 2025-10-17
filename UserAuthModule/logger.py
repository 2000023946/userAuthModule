import logging
import os
from pythonjsonlogger import jsonlogger

# -----------------------------
# Setup JSON structured logger
# -----------------------------

from abc import ABC, abstractmethod


class Loggable(ABC):
    @abstractmethod
    def get_logger(self) -> logging.Logger:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class ConsoleLogger(Loggable):
    def get_logger(self):
        logger = logging.getLogger("app_logger")
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(user_email)s %(ip)s %(env)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def name(self):
        return "console"


class FileLogger(Loggable):
    def get_logger(self):
        logger = logging.getLogger("app_logger")
        handler = logging.FileHandler("app.log")
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(user_email)s %(ip)s %(env)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def name(self):
        return "file"


class LoggerRegistry:
    _registry = {
        "console": ConsoleLogger(),
        "file": FileLogger(),
        # add third-party implementations here
    }

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        provider = cls._registry.get(name.lower())
        if not provider:
            raise ValueError(f"Unsupported logger: {name}")
        return provider.get_logger()


LOGGER_BACKEND = os.getenv("LOG_BACKEND", "console")
logger = LoggerRegistry.get_logger(LOGGER_BACKEND)
