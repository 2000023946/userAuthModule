from django.urls import path

from .views import (
    RegisterView,
    LogoutView,
    PasswordResetView,
    ThirdPartyRegisterView,
    LoginView,
    ThirdPartyLoginView,
    TokenRefreshView,
)

urlpatterns = [
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
]
