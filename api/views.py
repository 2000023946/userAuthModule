# api/views.py

# -----------------------------
# Standard Library
# -----------------------------
from abc import abstractmethod

# -----------------------------
# Third-Party / Django Imports
# -----------------------------
from django_redis import get_redis_connection  # type: ignore
from rest_framework import status  # type: ignore
from rest_framework.permissions import AllowAny, IsAuthenticated  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework.views import APIView  # type: ignore
# from rest_framework_simplejwt.tokens import RefreshToken  # type: ignore

# -----------------------------
# Local Imports
# -----------------------------
from .builder import LoginBuilder, PasswordResetBuilder, UserBuilder
from .services import (
    LoginFactory,
    PasswordResetFactory,
    RegistrationFactory,
    RegistrationService,
    ThirdPartyLoginFactory,
    ThirdPartyRegistrationFactory,
    ThirdPartyStrategySingleton,
)

# -----------------------------
# Views
# -----------------------------


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": f"Hello {request.user.email}"})


# -----------------------------
# 1️⃣ Register (Base Auth View)
# -----------------------------


class AuthViews(APIView):
    permission_classes = [AllowAny]  # anyone can attempt register via 3rd party

    mapping = {
        "create": status.HTTP_201_CREATED,
        "errors": status.HTTP_400_BAD_REQUEST,
        "message": status.HTTP_200_OK,
    }

    def get_code(self, result):
        key = next(iter(result.keys()))
        return self.mapping.get(key, status.HTTP_200_OK)

    def post(self, request):
        service = self.service()
        result = service.execute(
            request, self.builder(request=request), self.factoryState().build()
        )
        print("result", result)
        return Response(result, self.get_code(result))

    def get_valid_data(self, data):
        """
        Validate each key/value in data.
        Returns a tuple: (valid_data_dict, errors_dict)
        """
        errors = {}
        valid_data = {}

        for key, value in data.items():
            try:
                self.validate_single_data(key, value)
                valid_data[key] = value  # only keep if it passes validation
            except Exception as e:
                errors[key] = str(e)  # store the error message keyed by field name

        return valid_data, errors

    def validate_single_data(self, key, value):
        """
        Raises ValueError if invalid.
        """
        if not value:  # e.g. None, '', 0
            raise ValueError(f"Invalid argument '{value}' for '{key}' data")
        return True

    @property
    @abstractmethod
    def service(self):
        return RegistrationService

    @property
    @abstractmethod
    def builder(self):
        return UserBuilder

    @property
    @abstractmethod
    def factoryState(self):
        pass


class RegisterView(AuthViews):
    factoryState = RegistrationFactory


class PasswordResetView(AuthViews):
    builder = PasswordResetBuilder
    factoryState = PasswordResetFactory


# -----------------------------
# 2️⃣ Logout / Token Revocation
# -----------------------------


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            access_token = request.data.get("access")

            if refresh_token is None or access_token is None:
                print("error")
                return Response(
                    {"error": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            conn = get_redis_connection("default")

            print("old token")

            # blacklist them
            if conn.ttl(f"refresh_token:{refresh_token}") > 0:
                conn.set(
                    f"black_list:{refresh_token}",
                    refresh_token,
                    ex=conn.ttl(f"refresh_token:{refresh_token}"),
                )

            if conn.ttl(f"access_token:{access_token}") > 0:
                conn.set(
                    f"black_list:{access_token}",
                    access_token,
                    ex=conn.ttl(f"access_token:{access_token}"),
                )

            return Response(
                {"message": "Logout successful. Tokens invalidated."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(AuthViews):
    factoryState = LoginFactory
    builder = LoginBuilder


# -----------------------------
# 4️⃣ Third-Party Register/Login
# -----------------------------


class ThirdPartyView(AuthViews):
    def post(self, request):
        data, errors = self.get_valid_data(request.data)
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_info = ThirdPartyStrategySingleton.get_user_info(
                data["provider"], data["token"]
            )
        except Exception as exc:
            return Response({"errors": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return super().post(user_info)


class ThirdPartyRegisterView(ThirdPartyView):
    factoryState = ThirdPartyRegistrationFactory


class ThirdPartyLoginView(ThirdPartyView):
    factoryState = ThirdPartyLoginFactory
    builder = LoginBuilder


# -----------------------------
# 5️⃣ Access / Refresh endpoints
# -----------------------------


class TokenValidationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token_str = request.data.get("access")
        refresh_token_str = request.data.get("refresh")

        if not access_token_str or not refresh_token_str:
            return Response(
                {"detail": "Tokens required"}, status=status.HTTP_400_BAD_REQUEST
            )

        jti = request.session.get("jti")
        if not jti:
            return Response(
                {"detail": "Session expired"}, status=status.HTTP_400_BAD_REQUEST
            )

        conn = get_redis_connection("default")

        # check if blacklisted
        if conn.get(f"black_list:{access_token_str}") or conn.get(
            f"black_list:{refresh_token_str}"
        ):
            return Response(
                {"detail": "Expired Tokens"}, status=status.HTTP_400_BAD_REQUEST
            )

        if conn.get(f"access_token:{access_token_str}"):
            return Response(
                {"detail": "Success access token valid"}, status=status.HTTP_200_OK
            )

        if not conn.get(f"refresh_token:{refresh_token_str}"):
            return Response(
                {"detail": "Invalid Refresh Token"}, status=status.HTTP_400_BAD_REQUEST
            )

        # blacklist the refresh token
        conn.set(
            f"black_list:{refresh_token_str}",
            refresh_token_str,
            ex=conn.ttl(f"refresh_token:{refresh_token_str}"),
        )

        # make new tokens
        result = LoginBuilder(request).build()
        print(result)

        return Response({"details": result}, status=status.HTTP_200_OK)
