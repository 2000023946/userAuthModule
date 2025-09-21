from django.urls import path
from .views import *

from rest_framework_simplejwt.views import ( # type: ignore
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # refresh
    path('api/protected/', ProtectedView.as_view(), name='protected_view'),  # add this
]

urlpatterns += [
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('third-party-register/', ThirdPartyRegisterView.as_view(), name='third-party-register'),
    path('login/', LoginView.as_view(), name='login'),
    path('third-party-login/', ThirdPartyLoginView.as_view(), name='third-party-login'),
    path('token-validation/', TokenValidationView.as_view(), name='token-validation'),
]