import unittest
from unittest.mock import patch
from rest_framework.test import APIRequestFactory
from rest_framework import status
from api.views import AuthView, ThirdPartyAuthView


# --- Mock dependencies ---


class MockServiceCreate:
    def execute(self, data, builder, state_flow):
        return {"create": "created new item"}


class MockServiceError:
    def execute(self, data, builder, state_flow):
        return {"errors": "created new item"}


class MockBuilder:
    pass


class MockFactory:
    def build(self):
        return "mock_state_machine"


class MockLogger:
    def log(self, status_code, log_data):
        return f"logging {status_code}, data: {log_data}"


class MockMetrics:
    class counter:
        @staticmethod
        def increment(labels):
            pass

    class latency:
        @staticmethod
        def observe(elapsed, labels):
            pass


# --- Concrete test view subclass ---


class MockAuthView(AuthView):
    service_class = MockServiceCreate
    builder_class = MockBuilder
    factory_class = MockFactory
    logger = MockLogger
    metrics = MockMetrics


class MockAuthViewError(AuthView):
    service_class = MockServiceError
    builder_class = MockBuilder
    factory_class = MockFactory
    logger = MockLogger
    metrics = MockMetrics


# # --- Unit test ---
@patch("api.views.AuthView.service_class")
@patch("api.views.AuthView.builder_class")
@patch("api.views.AuthView.logger")
@patch("api.views.AuthView.factory_class")
class TestAuthView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_success(self, mock_factory, mock_logger, mock_builder, mock_service):
        view = MockAuthView.as_view()
        # Setup mocks
        mock_service.return_value = MockServiceCreate()
        mock_builder.return_value = MockBuilder()
        mock_factory.return_value = MockFactory()
        mock_logger.return_value = MockLogger()

        # Create request
        request = self.factory.post("/login/", {"username": "test"}, format="json")

        # Call view
        response = view(request)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("create", response.data)

    def test_error(self, mock_factory, mock_logger, mock_builder, mock_service):
        self.view = MockAuthViewError.as_view()
        # Setup mocks
        mock_service.return_value = MockServiceError()
        mock_builder.return_value = MockBuilder()
        mock_factory.return_value = MockFactory()
        mock_logger.return_value = MockLogger()

        # Create request
        request = self.factory.post("/login/", {"username": "test"}, format="json")

        # Call view
        response = self.view(request)

        print("resp", response)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)


class MockThirdPartyView(ThirdPartyAuthView):
    service_class = MockServiceCreate
    builder_class = MockBuilder
    factory_class = MockFactory
    logger = MockLogger


class TestThirdPartyAuthView(unittest.TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_create(self):
        self.view = MockAuthView.as_view()

        # Create request
        request = self.factory.post("/login/", {"username": "test"}, format="json")

        # Call view
        response = self.view(request)

        print("resp", response)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("create", response.data)

    def test_invalid_input(self):
        self.view = MockAuthViewError.as_view()

        # Create request
        request = self.factory.post("/login/", {"username": "test"}, format="json")

        # Call view
        response = self.view(request)

        print("resp", response)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
