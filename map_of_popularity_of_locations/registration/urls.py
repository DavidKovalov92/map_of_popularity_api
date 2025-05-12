from django.urls import path
from .views import (
    PasswordTokenCheckGenericView,
    RequestPasswordResetEmailGenericView,
    SetNewPasswordGenericView,
    SignUpView,
    LoginView,
    LogoutView,
)

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "request-reset-email/",
        RequestPasswordResetEmailGenericView.as_view(),
        name="request-reset-email",
    ),
    path(
        "reset-password/<uidb64>/<token>/",
        PasswordTokenCheckGenericView.as_view(),
        name="reset-password-confirm",
    ),
    path(
        "password-reset-complete/",
        SetNewPasswordGenericView.as_view(),
        name="password-reset-complete",
    ),
]
