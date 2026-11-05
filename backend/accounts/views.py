"""Authentication endpoints: register, login, logout, whoami."""

from __future__ import annotations

import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
    ensure_token,
)
from readyby_api.schema import AUTH_RESPONSE, ERROR_RESPONSE, JWT_RESPONSE, USER_RESPONSE

logger = logging.getLogger("accounts.auth")


def _credentials_payload(user) -> dict:
    """One login response carrying both supported credentials.

    The browser client keeps using the opaque ``token``; ``access``/``refresh``
    are there for any client that prefers stateless JWT. Both authenticate
    against the same user, so a client can be moved across without reissuing
    accounts.
    """
    refresh = RefreshToken.for_user(user)
    return {
        "token": ensure_token(user).key,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }


@extend_schema(
    tags=["auth"],
    summary="Register a customer account",
    request=RegisterSerializer,
    responses={
        201: AUTH_RESPONSE,
        400: ERROR_RESPONSE,
        429: ERROR_RESPONSE,
    },
)
class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("account.registered user_id=%s", user.pk)
        return Response(_credentials_payload(user), status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["auth"],
    summary="Exchange email and password for an API token",
    request=LoginSerializer,
    responses={200: AUTH_RESPONSE, 400: ERROR_RESPONSE, 429: ERROR_RESPONSE},
)
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        logger.info("account.login user_id=%s role=%s", user.pk, user.role)
        return Response(_credentials_payload(user))


@extend_schema(
    tags=["auth"],
    summary="Invalidate the current API token",
    description="The token is deleted, so the next request must sign in again.",
    request=None,
    responses={
        204: OpenApiResponse(description="The token is no longer valid."),
        401: ERROR_RESPONSE,
    },
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logger.info("account.logout user_id=%s", request.user.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["auth"],
    summary="Current signed-in user",
    responses={200: USER_RESPONSE, 401: ERROR_RESPONSE},
)
@extend_schema(
    tags=["auth"],
    summary="Update your own name, phone or password",
    description=(
        "Only the fields the account owner owns can be changed. `role`, `cafe`, "
        "`status` and the email address are not accepted here, so a crafted "
        "payload cannot promote an account or un-suspend it. Changing the "
        "password additionally requires `current_password`."
    ),
    request=ProfileUpdateSerializer,
    responses={200: USER_RESPONSE, 400: ERROR_RESPONSE, 401: ERROR_RESPONSE},
)
class MeView(APIView):
    """Read or edit the signed-in person's own account."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            instance=request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("account.profile_updated user_id=%s", user.pk)
        return Response(UserSerializer(user).data)


@extend_schema(
    tags=["auth"],
    summary="Exchange email and password for a JWT pair",
    description=(
        "Stateless alternative to `/api/auth/login/`. Returns a short-lived "
        "access token and a longer refresh token."
    ),
    request=LoginSerializer,
    responses={200: AUTH_RESPONSE, 400: ERROR_RESPONSE, 429: ERROR_RESPONSE},
)
class JwtLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        logger.info("account.login user_id=%s role=%s scheme=jwt", user.pk, user.role)
        return Response(_credentials_payload(user))


@extend_schema(
    tags=["auth"],
    summary="Exchange a refresh token for a new access token",
    request=None,
    responses={200: JWT_RESPONSE, 400: ERROR_RESPONSE, 401: ERROR_RESPONSE},
)
class JwtRefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        raw = (request.data.get("refresh") or "").strip()
        if not raw:
            return Response(
                {
                    "code": "validation_error",
                    "message": "A refresh token is required.",
                    "field_errors": {"refresh": ["A refresh token is required."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            refresh = RefreshToken(raw)
        except TokenError:
            return Response(
                {
                    "code": "not_authenticated",
                    "message": "That refresh token is no longer valid. Please sign in again.",
                    "field_errors": {},
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({"access": str(refresh.access_token)})