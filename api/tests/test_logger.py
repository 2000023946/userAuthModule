import unittest
from unittest.mock import patch
from rest_framework import status
from api.views import RegisterView


class TestRegisterLogger(unittest.TestCase):

    def setUp(self):
        self.logger_cls = RegisterView.logger

    @patch("api.loggers.logger")
    def test_register_logger_success(self, mock_logger):
        """Test that a successful registration logs with InfoLogger."""
        logger = self.logger_cls()
        result_data = {"create": {"email": "test@example.com"}, "request_id": "abc123"}

        # Act
        logger.log(status.HTTP_201_CREATED, result_data)

        # Assert
        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()

        args, kwargs = mock_logger.info.call_args
        self.assertIn("Registration success", args[0])
        self.assertEqual(kwargs["extra"]["user_email"], "test@example.com")
        self.assertEqual(kwargs["extra"]["request_id"], "abc123")

    @patch("api.loggers.logger")
    def test_register_logger_failure(self, mock_logger):
        """Test that a failed registration logs with WarningsLogger."""
        logger = self.logger_cls()
        error_data = {"errors": "Validation failed", "request_id": "req-456"}

        # Act
        logger.log(status.HTTP_400_BAD_REQUEST, error_data)

        # Assert
        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_not_called()
        mock_logger.error.assert_not_called()

        args, kwargs = mock_logger.warning.call_args
        self.assertIn("Registration failure", args[0])
        self.assertEqual(kwargs["extra"]["request_id"], "req-456")


if __name__ == "__main__":
    unittest.main()
