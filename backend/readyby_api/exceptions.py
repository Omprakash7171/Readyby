"""Uniform API error envelope.

Every failure the frontend can see has the same shape::

    {
      "code": "arrival_unavailable",
      "message": "The selected arrival time is no longer available.",
      "field_errors": {"arrival_time": ["..."]}
    }

The frontend maps ``code`` to copy and never renders a raw backend exception.
"""

from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("readyby.api")

GENERIC_SERVER_MESSAGE = (
    "Something went wrong. Please try again in a moment."
)
GENERIC_NOT_FOUND_MESSAGE = "We couldn't find that."
GENERIC_PERMISSION_MESSAGE = "You don't have access to that."
GENERIC_AUTH_MESSAGE = "Please sign in to continue."


class PilotAPIException(exceptions.APIException):
    """Base class for deliberate, user-facing API failures."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "bad_request"
    default_detail = GENERIC_SERVER_MESSAGE

    def __init__(
        self,
        detail: str | None = None,
        *,
        code: str | None = None,
        field_errors: dict[str, list[str]] | None = None,
        status_code: int | None = None,
    ) -> None:
        self.code = code or self.default_code
        self.field_errors = field_errors or {}
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail or self.default_detail, self.code)


class ConflictException(PilotAPIException):
    """The request was valid but conflicts with the current state."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"
    default_detail = GENERIC_SERVER_MESSAGE


class OrderPlacementException(PilotAPIException):
    """An order could not be placed. The message is safe to show a customer."""

    default_code = "order_rejected"
    default_detail = GENERIC_SERVER_MESSAGE


class InvalidTransitionException(ConflictException):
    """Someone tried to move an order through a state the machine forbids."""

    default_code = "invalid_transition"
    default_detail = "That status change is not allowed."


def _flatten_detail(detail) -> tuple[str | None, dict[str, list[str]]]:
    """Turn a DRF ``ErrorDetail`` structure into (message, field errors)."""
    if isinstance(detail, dict):
        field_errors: dict[str, list[str]] = {}
        messages: list[str] = []
        for key, value in detail.items():
            values = value if isinstance(value, list) else [value]
            texts = [str(item) for item in values]
            field_errors[str(key)] = texts
            messages.extend(texts)
        message = " ".join(messages) if messages else None
        return message, field_errors

    if isinstance(detail, list):
        texts = [str(item) for item in detail]
        return (texts[0] if texts else None), {}

    return str(detail), {}


def _code_for_status(status_code: int) -> str:
    return {
        status.HTTP_400_BAD_REQUEST: "validation_error",
        status.HTTP_401_UNAUTHORIZED: "not_authenticated",
        status.HTTP_403_FORBIDDEN: "forbidden",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
        status.HTTP_409_CONFLICT: "conflict",
        status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
    }.get(status_code, "server_error")


def _message_for(status_code: int, fallback: str | None) -> str:
    if fallback:
        return fallback
    return {
        status.HTTP_401_UNAUTHORIZED: GENERIC_AUTH_MESSAGE,
        status.HTTP_403_FORBIDDEN: GENERIC_PERMISSION_MESSAGE,
        status.HTTP_404_NOT_FOUND: GENERIC_NOT_FOUND_MESSAGE,
        status.HTTP_429_TOO_MANY_REQUESTS: "Too many attempts. Please wait a moment and try again.",
    }.get(status_code, GENERIC_SERVER_MESSAGE)


def api_exception_handler(exc, context):
    """DRF exception handler that always returns the ReadyBy error envelope."""
    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception(
            "unhandled_api_exception path=%s",
            context.get("request").path if context.get("request") else "unknown",
        )
        return Response(
            {"code": "server_error", "message": GENERIC_SERVER_MESSAGE, "field_errors": {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, PilotAPIException):
        code = exc.code
        message = _message_for(response.status_code, str(exc.detail))
        field_errors = exc.field_errors
    else:
        message, field_errors = _flatten_detail(response.data)
        code = _code_for_status(response.status_code)
        if isinstance(exc, (exceptions.AuthenticationFailed, exceptions.NotAuthenticated)):
            code = "not_authenticated"
            message = GENERIC_AUTH_MESSAGE
        elif isinstance(exc, (exceptions.PermissionDenied, DjangoPermissionDenied)):
            code = "forbidden"
            message = GENERIC_PERMISSION_MESSAGE
        elif isinstance(exc, Http404):
            code = "not_found"
            message = GENERIC_NOT_FOUND_MESSAGE
        elif isinstance(exc, DjangoValidationError):
            code = "validation_error"
            message = GENERIC_SERVER_MESSAGE

    response.data = {
        "code": code,
        "message": _message_for(response.status_code, message),
        "field_errors": field_errors,
    }
    return response


def friendly(field: str, message: str) -> dict[str, list[str]]:
    return {field: [message]}