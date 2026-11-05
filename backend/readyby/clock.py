"""Clock helpers.

The API sends timestamps as ISO-8601 and *also* sends a pre-formatted label so
the frontend never has to re-implement time formatting (and never disagrees
about "10:30 AM").
"""

from __future__ import annotations

from datetime import datetime, timedelta

from django.utils import timezone


def now() -> datetime:
    """Timezone-aware current time."""
    return timezone.now()


def local(moment: datetime) -> datetime:
    """The moment rendered in the configured site timezone."""
    if timezone.is_naive(moment):
        moment = timezone.make_aware(moment, timezone.get_default_timezone())
    return timezone.localtime(moment)


def _twelve_hour(moment: datetime) -> str:
    """``10:30 AM`` on every platform.

    ``%I`` with a ``-`` modifier is a glibc extension and raises on Windows, so
    the hour is stripped of its leading zero by hand instead.
    """
    hour = moment.strftime("%I").lstrip("0") or "0"
    suffix = moment.strftime("%p")
    return f"{hour}:{moment.strftime('%M')} {suffix}"


def format_clock(moment: datetime) -> str:
    """``10:30 AM`` — unambiguous 12-hour clock, no leading zero."""
    return _twelve_hour(local(moment))


def format_day_clock(moment: datetime) -> str:
    """``Today 10:30 AM`` / ``Tomorrow 09:00 AM`` / ``Fri 09:00 AM``."""
    target = local(moment)
    today = local(now()).date()
    delta = (target.date() - today).days
    if delta == 0:
        prefix = "Today"
    elif delta == 1:
        prefix = "Tomorrow"
    else:
        prefix = target.strftime("%a")
    return f"{prefix} {_twelve_hour(target)}"


def format_date(moment: datetime) -> str:
    """``2 Oct 2026``."""
    return f"{local(moment).day} {local(moment).strftime('%b %Y')}"


def minutes_between(start: datetime, end: datetime) -> int:
    """Whole minutes from ``start`` to ``end``, rounded down."""
    return int((end - start).total_seconds() // 60)


def add_minutes(moment: datetime, minutes: int) -> datetime:
    return moment + timedelta(minutes=minutes)