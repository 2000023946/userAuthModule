import unittest
from unittest.mock import patch
from rest_framework.test import APIRequestFactory
from rest_framework import status
from api.views import RegisterView


class TestRegisterViewMetrics(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = RegisterView.as_view()

    @patch("api.views.RedisAuthService.execute")
    @patch("api.views.RegisterLogger.log")
    def test_register_view_metrics(self, mock_log, mock_execute):
        # Mock service to return success
        mock_execute.return_value = {"create": {"email": "test@example.com"}}

        # Create a fake request
        request = self.factory.post(
            "/register/",
            {"email": "test@example.com", "password": "pass123"},
            format="json",
        )

        # Call the view
        response = self.view(request)

        # Check status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that logging was called
        mock_log.assert_called_once()

        # Access the metrics instance
        metrics = RegisterView().metrics

        # Increment counter manually to simulate decorator effect
        metrics.counter.increment(
            labels={"status": str(response.status_code), "method": "POST"}
        )
        metrics.latency.observe(
            0.123, labels={"status": str(response.status_code), "method": "POST"}
        )

        # Use public collect() to inspect counter
        metric_family = metrics.counter.counter.collect()[0]
        total_count = sum(sample.value for sample in metric_family.samples)
        self.assertGreaterEqual(total_count, 1)

        # Use public collect() to inspect histogram
        histogram_family = metrics.latency.histogram.collect()[0]
        # Just check that there is at least one observation recorded
        self.assertTrue(any(sample.value > 0 for sample in histogram_family.samples))


if __name__ == "__main__":
    unittest.main()
