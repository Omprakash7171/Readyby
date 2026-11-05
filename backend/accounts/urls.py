from django.urls import path

from .views import (
    JwtLoginView,
    JwtRefreshView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    # GET reads the signed-in account; PATCH edits the fields the owner owns.
    path("me/", MeView.as_view(), name="auth-me"),
    # Stateless alternative to the opaque token, for clients that prefer JWT.
    path("token/", JwtLoginView.as_view(), name="auth-jwt-login"),
    path("token/refresh/", JwtRefreshView.as_view(), name="auth-jwt-refresh"),
]