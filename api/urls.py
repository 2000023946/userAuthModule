from django.urls import path

from .views import (
    RegisterView,
    LogoutView,
    PasswordResetView,
    ThirdPartyRegisterView,
    LoginView,
    ThirdPartyLoginView,
    TokenRefreshView,
    ValidateTokenView,
)

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse


def metrics_view(request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


urlpatterns = [
    path("metrics/", metrics_view),  # Prometheus scrapes this
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path(
        "third-party-register/",
        ThirdPartyRegisterView.as_view(),
        name="third-party-register",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("third-party-login/", ThirdPartyLoginView.as_view(), name="third-party-login"),
    path("token-refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("validate-token/", ValidateTokenView.as_view(), name="validate-token"),
]
