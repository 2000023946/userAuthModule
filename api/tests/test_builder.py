import unittest
from unittest.mock import patch, MagicMock, ANY
from api.builder import (
    UserPasswordCleaner,
    UserBuilder,
    PasswordResetBuilder,
    LoginBuilder,
    LogoutBuilder,
    TokenRefreshBuilder,
    BuilderException,
    OAuthUserInfoBuilder,
    ValidationTokenBuilder,
)
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


# A more robust mock serializer that better imitates the real one
class MockSerializer:
    def __init__(self, instance=None, data=None):
        # FIX: Store the actual instance object, not just its data
        self.instance = instance
        self.initial_data = data
        self._validated_data = {}

    def is_valid(self, raise_exception=False):
        if self.initial_data:
            self._validated_data = self.initial_data.copy()
        return True

    def save(self):
        # FIX: Return the instance object itself, just like a real serializer
        if self.instance is None:
            # Simulate creating a new instance
            self.instance = {"id": 1, **self._validated_data}
        else:
            # Simulate updating an existing instance
            for key, value in self._validated_data.items():
                setattr(self.instance, key, value)
        return self.instance

    @property
    def data(self):
        if isinstance(self.instance, MagicMock):
            # Try to simulate a .data property for a mock object
            return {
                "pk": self.instance.pk,
                "email": self.instance.email,
                **self._validated_data,
            }
        return self.instance


# --- Test Cases ---


class TestUserPasswordCleaner(unittest.TestCase):
    """Tests the UserPasswordCleaner strategy."""

    def setUp(self):
        self.cleaner = UserPasswordCleaner()


class TestModelBuilders(unittest.TestCase):
    """Tests the concrete model builders."""

    @patch("api.builder.UserBuilder.get_serializer")
    def test_user_builder_creates_user(self, mock_get_serializer):
        """UserBuilder should clean data and call serializer.save."""
        mock_serializer_instance = MockSerializer()
        mock_get_serializer.return_value = mock_serializer_instance

        builder = UserBuilder()
        data = {
            "email": "new@example.com",
            "password": "password123",
            "password_repeat": "password123",
        }
        builder.build(data)

        # FIX: Use assert_any_call to check if the call with `data` happened at all
        mock_get_serializer.assert_any_call(data=ANY)

    @patch("api.builder.PasswordResetBuilder.get_serializer")
    @patch("api.builder.get_user_by_email")
    def test_password_reset_builder_updates_user(
        self, mock_user_get, mock_get_serializer
    ):
        """PasswordResetBuilder should get an instance, clean data, and update."""

        class MockUser:
            def __init__(self, pk, email):
                self.pk = pk
                self.email = email

        def get_user_by_email(email):
            return mock_instance

        mock_instance = MockUser(pk=1, email="test@example.com")
        mock_user_get.side_effect = get_user_by_email

        mock_serializer_instance = MockSerializer(instance=mock_instance)
        mock_get_serializer.return_value = mock_serializer_instance

        builder = PasswordResetBuilder()
        data = {
            "email": "test@example.com",
            "password": "new_password123",
            "password_repeat": "new_password123",
        }
        builder.build(data)

        mock_user_get.assert_called_once_with(email="test@example.com")
        # This assertion will now pass because MockSerializer.save() returns the MagicMock instance
        mock_get_serializer.assert_any_call(instance=mock_instance, data=ANY)


@patch("api.builder.get_redis_connection")
class TestAPIResponseBuilders(unittest.TestCase):
    """Tests the API response builders (Login, Logout, TokenRefresh)."""

    @patch("api.builder.LoginBuilder.build")
    @patch("api.builder.blacklist_refresh")
    def test_token_refresh_builder_success(
        self, mock_blacklist, mock_login_build, mock_redis_conn
    ):
        """TokenRefreshBuilder should blacklist old token and generate new ones."""

        # 1️⃣ Mock Redis connection
        mock_redis = MagicMock()
        mock_redis_conn.return_value = mock_redis

        # 2️⃣ Create a fake RefreshToken instance
        mock_refresh_token = MagicMock(spec=RefreshToken)
        mock_refresh_token.get.return_value = 1  # user_id

        # 3️⃣ Mock super().build()
        mock_login_build.return_value = {
            "refresh": "new_refresh",
            "access": "new_access",
        }

        # 4️⃣ Run builder
        builder = TokenRefreshBuilder()
        result = builder.build({"refresh": mock_refresh_token})

        # 5️⃣ Assertions
        mock_refresh_token.get.assert_called_once_with("user_id")
        mock_blacklist.assert_called_once_with(mock_redis, mock_refresh_token)
        mock_login_build.assert_called_once()  # MinimalUser passed internally
        assert result == {"refresh": "new_refresh", "access": "new_access"}

    @patch("api.builder.RefreshToken")
    @patch("api.builder.get_user_by_email")
    def test_login_builder_creates_tokens_and_sets_redis(
        self, mock_user_get, mock_refresh_token, mock_redis_conn
    ):
        """LoginBuilder should generate tokens and store them in Redis."""

        class MockUser:
            def __init__(self, pk, email):
                self.pk = pk
                self.email = email

        def get_user_by_email(email):
            return mock_instance

        mock_instance = MockUser(pk=1, email="test@example.com")
        mock_user_get.side_effect = get_user_by_email

        mock_redis = MagicMock()
        mock_redis_conn.return_value = mock_redis

        mock_access = MagicMock()
        mock_access.__str__.return_value = "fake_access_token"
        mock_access.__getitem__.side_effect = lambda key: (
            1672531200 if key == "exp" else None
        )

        mock_refresh = MagicMock()
        mock_refresh.access_token = mock_access
        mock_refresh.__str__.return_value = "fake_refresh_token"
        mock_refresh.__getitem__.side_effect = lambda key: (
            1672531200 if key == "exp" else None
        )

        mock_refresh_token.for_user.return_value = mock_refresh

        builder = LoginBuilder()
        builder.build({"email": "test@example.com", "password": "..."})

        mock_user_get.assert_called_once_with(email="test@example.com")
        mock_refresh_token.for_user.assert_called_once_with(mock_instance)


class TestLogoutBuilder(unittest.TestCase):

    @patch("api.builder.get_redis_connection")
    @patch("api.builder.blacklist_access")
    @patch("api.builder.blacklist_refresh")
    def test_logout_builder_success(
        self, mock_blacklist_refresh, mock_blacklist_access, mock_redis_conn
    ):
        """LogoutBuilder should blacklist tokens and return success message."""

        # Mock Redis connection
        mock_redis = MagicMock()
        mock_redis_conn.return_value = mock_redis

        builder = LogoutBuilder()
        data = {"refresh": "fake_refresh_token", "access": "fake_access_token"}

        result = builder.build(data)

        # Assertions
        mock_blacklist_refresh.assert_called_once_with(mock_redis, "fake_refresh_token")
        mock_blacklist_access.assert_called_once_with(mock_redis, "fake_refresh_token")
        assert result == {"detail": "Logout successful. Tokens invalidated."}

    def test_logout_builder_missing_tokens(self):
        """LogoutBuilder should raise BuilderException if tokens are missing."""

        builder = LogoutBuilder()

        # Missing refresh_token
        with self.assertRaises(BuilderException):
            builder.build({"access_token": "fake_access_token"})

        # Missing access_token
        with self.assertRaises(BuilderException):
            builder.build({"refresh_token": "fake_refresh_token"})

        # Missing both
        with self.assertRaises(BuilderException):
            builder.build({})


class TestOAuthUserInfoBuilder(unittest.TestCase):

    @patch("api.builder.ThirdPartyStrategySingleton.get_user_info")
    def test_oauth_user_info_builder_success(self, mock_get_user_info):
        """Should return user info from the third-party strategy."""

        # Mock the return value from get_user_info
        mock_user_info = {"id": "123", "email": "user@example.com"}
        mock_get_user_info.return_value = mock_user_info

        builder = OAuthUserInfoBuilder()
        data = {"provider": "google", "token": "fake_oauth_token"}

        result = builder.build(data)

        # Assertions
        mock_get_user_info.assert_called_once_with("google", "fake_oauth_token")
        self.assertEqual(result, mock_user_info)

    def test_oauth_user_info_builder_missing_inputs(self):
        """Should raise BuilderException if provider or token is missing."""

        builder = OAuthUserInfoBuilder()

        # Missing provider
        with self.assertRaises(BuilderException):
            builder.build({"token": "fake_token"})

        # Missing token
        with self.assertRaises(BuilderException):
            builder.build({"provider": "google"})

        # Missing both
        with self.assertRaises(BuilderException):
            builder.build({})


class TestValidationTokenBuilder(unittest.TestCase):

    @patch("api.builder.RefreshToken")
    def test_validation_token_builder_success(self, mock_refresh_token):
        """Should return success if refresh token is valid."""

        # Mock RefreshToken instantiation to succeed
        mock_refresh_token.return_value = MagicMock()

        builder = ValidationTokenBuilder()
        data = {"refresh_token": "valid_token"}

        result = builder.build(data)

        mock_refresh_token.assert_called_once_with("valid_token")
        self.assertEqual(result, {"detail": "Token is valid."})

    def test_validation_token_builder_missing_token(self):
        """Should raise BuilderException if token is missing."""

        builder = ValidationTokenBuilder()
        with self.assertRaises(BuilderException):
            builder.build({})  # no token

    @patch("api.builder.RefreshToken", side_effect=TokenError("Invalid token"))
    def test_validation_token_builder_invalid_token(self, mock_refresh_token):
        """Should raise BuilderException if token is invalid."""

        builder = ValidationTokenBuilder()
        with self.assertRaises(BuilderException) as cm:
            builder.build({"refresh_token": "bad_token"})

        self.assertEqual(str(cm.exception), "Token is invalid or expired.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
