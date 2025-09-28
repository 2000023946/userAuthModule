from abc import ABC

import datetime

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import CustomUser
from .serializer import UserSerializer
from .hasher import hash_token


class Buildable(ABC):
    def __init__(self, request):
        self.session = None
        if hasattr(request, "session"):
            self.data = request.session.get(self.name, {})
            request.session[self.name] = self.data
            self.session = request.session
        else:
            self.data = request

    def register(self, key, value):
        print("register this", key, value)
        self.data[key] = value

    def build(self):
        """
        If instance is None → create new object.
        If instance is provided → update existing object.
        """
        instance = self.get_instance()
        self.validate_data()
        serializer_class = self.serializer_class  # class, not instance

        if instance:
            user = serializer_class().update(instance, self.data)
        else:
            user = serializer_class().create(self.data)

        self.decouple()

        # Serialize the user instance for JSON output
        return serializer_class(user).data  # instantiate serializer class here

    def decouple(self):
        if self.session:
            del self.session[self.name]

    def validate_data(self):
        self.data = self.data

    def get_instance(self):
        return


class UserMainBuilder(Buildable):
    serializer_class = UserSerializer

    def validate_data(self):
        super().validate_data()
        self.data = {k: v for k, v in self.data.items() if k != "password_repeat"}
        # Hash the password if it exists
        if "password" in self.data:
            self.data["password"] = make_password(self.data["password"])


class UserBuilder(UserMainBuilder):
    name = "UserBuilder"


class PasswordResetBuilder(UserMainBuilder):
    name = "PasswordResetBuilder"

    def get_instance(self):
        print(self.data, "getting the user")
        return CustomUser.objects.get(email=self.data["email"])


class LoginBuilder(Buildable):
    name = "LoginBuilder"

    def build(self):
        user = CustomUser.objects.get(email=self.data["email"])
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Use Python's datetime.timezone.utc instead of timezone.utc
        refresh_exp = datetime.datetime.fromtimestamp(
            refresh["exp"], tz=datetime.timezone.utc
        )
        access_exp = datetime.datetime.fromtimestamp(
            access["exp"], tz=datetime.timezone.utc
        )

        seconds_until_refresh_exp = int((refresh_exp - timezone.now()).total_seconds())
        seconds_until_access_exp = int((access_exp - timezone.now()).total_seconds())

        # Hash tokens for storage
        refresh_token_hash = hash_token(str(refresh))
        access_token_hash = hash_token(str(access))

        # Store hashes in Redis with TTL
        conn = get_redis_connection("default")
        conn.set(
            f"refresh_token:{refresh_token_hash}",
            refresh_token_hash,
            ex=seconds_until_refresh_exp,
        )
        conn.set(
            f"access_token:{access_token_hash}",
            access_token_hash,
            ex=seconds_until_access_exp,
        )

        # Remove builder from session
        self.decouple()

        # Return raw tokens to client
        return {
            "refresh": str(refresh),
            "access": str(access),
            "email": self.data["email"],
        }
