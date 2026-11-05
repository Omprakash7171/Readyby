"""Field validators shared by more than one app.

Kept here so the customer account and the café that takes their order agree on
what a usable phone number or timezone looks like, instead of each app inventing
its own rule.

Validation runs in three places and they must not disagree:

* the database (via ``validators=`` on the model field, used by ``full_clean``
  and therefore by the Django admin),
* the DRF serializer (so the API answers with a field error), and
* the browser form (for immediate feedback).

All three call the functions below.
"""

from __future__ import annotations

import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

#: A phone number is stored as typed, in a small subset of human formats.
#:
#: Accepted: an optional leading ``+``, then digits, with spaces, dots, dashes
#: and parentheses allowed as separators, and an optional extension. Rejected:
#: letters, several ``+`` signs, and anything empty once separators are removed.
#: Digits only are the common case; the separators keep typed numbers readable.
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\s().-]{4,19}[0-9]$")

#: Longest phone string we keep. Matches the column width.
MAX_PHONE_LENGTH = 32

PHONE_HELP = _("Digits, spaces, +, () and - only, 6 to 20 characters.")


def validate_phone(value: str) -> None:
    """Reject anything that is not a plausibly dialable phone number.

    An empty value is allowed: a phone number is optional everywhere ReadyBy
    asks for one, so only the model's ``blank=True`` rule forbids it.
    """
    if value in (None, ""):
        return

    text = str(value).strip()
    if not text:
        return

    if len(text) > MAX_PHONE_LENGTH:
        raise ValidationError(
            "%(value)s is too long. %(help)s",
            params={"value": len(text), "help": PHONE_HELP},
            code="phone_too_long",
        )

    if not PHONE_PATTERN.match(text):
        raise ValidationError(
            "%(value)s is not a usable phone number. %(help)s",
            params={"value": text, "help": PHONE_HELP},
            code="phone_invalid",
        )


def is_valid_timezone(name: str) -> bool:
    """True when ``name`` is a timezone the platform can resolve."""
    if not name:
        return False
    try:
        ZoneInfo(str(name))
    except (ZoneInfoNotFoundError, ValueError, KeyError, ModuleNotFoundError):
        return False
    return True


def validate_timezone(value: str) -> None:
    """Reject a timezone the server cannot resolve.

    A café's opening hours are wall-clock facts for its own locality, so the
    zone has to be a real IANA name (``Europe/London``). Anything unresolvable
    would silently fall back to the site timezone and quietly book the wrong
    hours.
    """
    if value in (None, ""):
        return

    if not is_valid_timezone(value):
        raise ValidationError(
            "%(value)s is not a known timezone. Use an IANA name such as "
            "Europe/London or America/New_York.",
            params={"value": value},
            code="timezone_invalid",
        )


__all__ = [
    "MAX_PHONE_LENGTH",
    "PHONE_HELP",
    "PHONE_PATTERN",
    "is_valid_timezone",
    "validate_phone",
    "validate_timezone",
]