import jwt
import unittest
from unittest.mock import patch

from api.validators import (
    ValidationError,
    UsernameValidator,
    EmailValidator,
    PasswordValidator,
    EmailResetValidator,
    TokenValidator,
    AccessTokenValidator,
    RefreshTokenValidator,
    ProviderValidator,
    OAuthTokenValidator,
    UserRegistrationValidator,
    PasswordResetValidator,
    TokenRefreshValidator,
)

from ..utils import hash_token


# -------------------------
# USERNAME VALIDATOR
# -------------------------
class TestUsernameValidator(unittest.TestCase):
    @patch("api.validators.QueryCacheSingleton.get_or_set", return_value=False)
    def test_username_validator_valid(self, mock_cache):
        validator = UsernameValidator()
        self.assertTrue(validator.validate("valid_user123"))

    @patch("api.validators.QueryCacheSingleton.get_or_set", return_value=True)
    def test_username_already_taken(self, mock_cache):
        validator = UsernameValidator()
        with self.assertRaises(ValidationError):
            validator.validate("existing_user")

    def test_username_invalid_length(self):
        v = UsernameValidator()
        with self.assertRaises(ValidationError):
            v.validate("ab")

    def test_username_invalid_chars(self):
        v = UsernameValidator()
        with self.assertRaises(ValidationError):
            v.validate("user@@")


# -------------------------
# EMAIL VALIDATOR
# -------------------------
class TestEmailValidator(unittest.TestCase):
    @patch("api.validators.get_user_by_email", return_value=None)
    def test_email_validator_valid(self, mock_user):
        v = EmailValidator()
        self.assertTrue(v.validate("test@example.com"))

    @patch("api.validators.get_user_by_email", return_value=True)
    def test_email_already_registered(self, mock_user):
        v = EmailValidator()
        with self.assertRaises(ValidationError):
            v.validate("taken@example.com")

    def test_email_invalid_format(self):
        v = EmailValidator()
        with self.assertRaises(ValidationError):
            v.validate("bademail.com")


# -------------------------
# PASSWORD VALIDATOR
# -------------------------
class TestPasswordValidator(unittest.TestCase):
    def test_password_validator_valid(self):
        v = PasswordValidator()
        self.assertTrue(v.validate("GoodPass1"))

    def test_password_too_short(self):
        v = PasswordValidator()
        with self.assertRaises(ValidationError):
            v.validate("Abc1")

    def test_password_no_number(self):
        v = PasswordValidator()
        with self.assertRaises(ValidationError):
            v.validate("Password")

    def test_password_no_uppercase(self):
        v = PasswordValidator()
        with self.assertRaises(ValidationError):
            v.validate("password1")


# -------------------------
# EMAIL RESET VALIDATOR
# -------------------------
class TestEmailResetValidator(unittest.TestCase):
    @patch("api.validators.get_user_by_email", return_value=True)
    def test_email_reset_valid(self, mock_user):
        v = EmailResetValidator()
        self.assertTrue(v.validate("user@example.com"))

    @patch("api.validators.get_user_by_email", return_value=None)
    def test_email_reset_no_user(self, mock_user):
        v = EmailResetValidator()
        with self.assertRaises(ValidationError):
            v.validate("nouser@example.com")


# -------------------------
# TOKEN VALIDATORS
# -------------------------
class TestTokenValidator(unittest.TestCase):
    def test_token_validator_valid(self):
        v = TokenValidator()
        token = "aaa.bbb.ccc"
        self.assertTrue(v.validate(token))

    def test_token_validator_invalid_format(self):
        v = TokenValidator()
        with self.assertRaises(ValidationError):
            v.validate("invalidtoken")


# -------------------------
# ACCESS TOKEN VALIDATOR
# -------------------------
class TestAccessTokenValidator(unittest.TestCase):
    @patch("api.validators.get_redis_connection")
    @patch("jwt.decode", return_value={"some": "payload"})
    def test_access_token_valid(self, mock_decode, mock_redis):
        mock_redis.return_value.get.return_value = None
        v = AccessTokenValidator()
        self.assertTrue(v.validate("aaa.bbb.ccc"))

    @patch("api.validators.get_redis_connection")
    def test_access_token_blacklisted(self, mock_redis):
        mock_redis.return_value.get.return_value = True
        v = AccessTokenValidator()
        with self.assertRaises(ValidationError):
            v.validate("aaa.bbb.ccc")

    @patch("api.validators.get_redis_connection")
    @patch("jwt.decode", side_effect=jwt.ExpiredSignatureError)
    def test_access_token_expired(self, mock_decode, mock_redis):
        mock_redis.return_value.get.return_value = None
        v = AccessTokenValidator()
        with self.assertRaises(ValidationError):
            v.validate("aaa.bbb.ccc")


# -------------------------
# REFRESH TOKEN VALIDATOR
# -------------------------
class TestRefreshTokenValidator(unittest.TestCase):
    class MockRefreshToken:
        def __init__(self, token):
            if token == "bad":
                raise ValidationError("Invalid token")

    @patch("api.validators.get_redis_connection")
    @patch("api.validators.RefreshToken")
    def test_refresh_token_valid(self, mock_refresh, mock_redis):
        mock_refresh.return_value = self.MockRefreshToken("good")
        mock_redis.return_value.get.return_value = None
        v = RefreshTokenValidator()
        self.assertTrue(v.validate("good"))

    @patch("api.validators.get_redis_connection")
    def test_refresh_token_blacklisted(self, mock_redis):
        mock_redis.return_value.get.return_value = True
        v = RefreshTokenValidator()
        with self.assertRaises(ValidationError):
            v.validate("aaa.bbb.ccc")

    @patch("api.validators.get_redis_connection")
    @patch("api.validators.RefreshToken")
    def test_refresh_token_invalid(self, mock_refresh, mock_redis):
        mock_refresh.side_effect = self.MockRefreshToken
        mock_redis.return_value.get.return_value = None
        v = RefreshTokenValidator()
        with self.assertRaises(ValidationError):
            v.validate("bad")


# -------------------------
# PROVIDER VALIDATOR
# -------------------------
class TestProviderValidator(unittest.TestCase):
    @patch("api.o_auth_start.ThirdPartyStrategySingleton.strategies", {"google": None})
    def test_provider_valid(self):
        v = ProviderValidator()
        self.assertTrue(v.validate("google"))

    @patch("api.o_auth_start.ThirdPartyStrategySingleton.strategies", {"google": None})
    def test_provider_invalid(self):
        v = ProviderValidator()
        with self.assertRaises(ValidationError):
            v.validate("twitter")


# -------------------------
# OAUTH TOKEN VALIDATOR
# -------------------------
class TestOAuthTokenValidator(unittest.TestCase):
    def test_oauth_token_validator_valid(self):
        v = OAuthTokenValidator()
        self.assertTrue(v.validate("token123"))

    def test_oauth_token_validator_empty(self):
        v = OAuthTokenValidator()
        with self.assertRaises(ValidationError):
            v.validate("")


# -------------------------
# COMPLETE STATE VALIDATORS
# -------------------------
class TestUserRegistrationValidator(unittest.TestCase):
    def test_user_registration_valid(self):
        v = UserRegistrationValidator()
        data = {"username": "validuser", "email": "user@example.com"}
        self.assertRaises(ValidationError, v.validate, data)

    def test_user_registration_empty_data(self):
        v = UserRegistrationValidator()
        with self.assertRaises(ValidationError):
            v.validate({})

    def test_user_registration_similar_fields(self):
        v = UserRegistrationValidator()
        data = {"username": "user123", "email": "user123@example.com"}
        with self.assertRaises(ValidationError):
            v.validate(data)

    def test_token_refresh_validator(self):
        v = TokenRefreshValidator()
        self.assertTrue(v.validate({"refresh": "aaa.bbb.ccc"}))

    def test_password_repeat_match(self):
        v = PasswordResetValidator()
        data = {"password": hash_token("GoodPass1"), "password_repeat": "GoodPass1"}
        self.assertTrue(v.validate(data))

    def test_password_repeat_mismatch(self):
        v = PasswordResetValidator()
        with self.assertRaises(ValidationError):
            v.validate({"password": "GoodPass1", "confirm": "WrongPass"})

    def test_password_repeat_no_data(self):
        v = PasswordResetValidator()
        with self.assertRaises(ValidationError):
            v.validate({})
