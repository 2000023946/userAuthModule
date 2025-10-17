import unittest
from unittest.mock import patch, MagicMock
from api.o_auth_start import ThirdPartyStrategySingleton


class TestThirdPartyStrategy(unittest.TestCase):

    @patch("api.o_auth_start.requests.get")
    def test_google_strategy_success(self, mock_get):
        # Mock the response returned by requests.get
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "email": "momo@example.com",
            "name": "momo"
        }
        mock_get.return_value = mock_resp

        # Run the strategy
        result = ThirdPartyStrategySingleton.get_user_info("google", "fake_token")

        # Verify the output
        self.assertEqual(result["email"], "momo@example.com")
        self.assertEqual(result["username"], "momo")

        # Ensure requests.get was called correctly
        mock_get.assert_called_once_with(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": "fake_token"}
        )

    @patch("api.o_auth_start.requests.get")
    def test_google_strategy_invalid_token(self, mock_get):
        # Mock a failed API response
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            ThirdPartyStrategySingleton.get_user_info("google", "bad_token")

        self.assertIn("Invalid Google token", str(ctx.exception))
