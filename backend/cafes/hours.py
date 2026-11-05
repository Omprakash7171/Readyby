"""Opening-hours parsing and open/closed evaluation.

Opening hours are stored as a plain JSON object so a café can have split shifts::

    {"mon": [["07:30", "11:30"], ["14:00", "18:00"]], "tue": [["07:30", "18:00"]]}

A range whose closing time is at or before its opening time is treated as
running past midnight into the following day.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from django.utils import timezone

DAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

WEEKDAY_INDEX = {key: index for index, key in enumerate(DAY_KEYS)}

DEFAULT_OPENING_HOURS: dict[str, list[list[str]]] = {
    "mon": [["07:00", "18:00"]],
    "tue": [["07:00", "18:00"]],
    "wed": [["07:00", "18:00"]],
    "thu": [["07:00", "18:00"]],
    "fri": [["07:00", "18:00"]],
    "sat": [["08:00", "18:00"]],
    "sun": [["08:00", "17:00"]],
}

CLOSING_SOON_MINUTES = 30


def default_opening_hours() -> dict[str, list[list[str]]]:
    """A fresh copy of the default hours.

    Declared as a named function (not a lambda) so migrations can serialise it.
    """
    return {
        day: [[window[0], window[1]] for window in windows]
        for day, windows in DEFAULT_OPENING_HOURS.items()
    }


@dataclass(frozen=True)
class OpeningWindow:
    opens: time
    closes: time

    @property
    def spans_midnight(self) -> bool:
        return self.closes <= self.opens


@dataclass(frozen=True)
class OpenState:
    """Why a café is (or is not) currently open."""

    key: str
    label: str
    is_open: bool

    @property
    def can_order(self) -> bool:
        return self.is_open


OPEN = OpenState("open", "Open now", True)
CLOSING_SOON = OpenState("closing-soon", "Closing soon", True)
CLOSED = OpenState("closed", "Closed", False)


def _parse_clock(raw: str) -> time:
    hour, _, minute = raw.strip().partition(":")
    return time(hour=int(hour), minute=int(minute or 0))


def _wall_clock(moment: datetime) -> datetime:
    """The moment as a naive wall-clock time in the site's timezone.

    Opening hours are wall-clock facts ("closes at 5pm wherever you are"), so
    the café's own day is what matters, not the caller's offset.
    """
    if timezone.is_naive(moment):
        return moment
    return timezone.localtime(moment).replace(tzinfo=None)


def _in_site_timezone(moment: datetime) -> datetime:
    """Re-attach the site's timezone so callers get aware datetimes back.

    Everything returned by this module must be comparable with the aware
    datetimes the rest of the app uses.
    """
    return timezone.make_aware(moment, timezone.get_default_timezone())


def parse_opening_hours(raw: object) -> dict[int, list[OpeningWindow]]:
    """Normalise stored hours into ``{weekday index: [OpeningWindow, ...]}``."""
    windows: dict[int, list[OpeningWindow]] = {index: [] for index in range(7)}
    if not isinstance(raw, dict):
        return windows

    for key, ranges in raw.items():
        index = WEEKDAY_INDEX.get(str(key).strip().lower()[:3])
        if index is None or not isinstance(ranges, list):
            continue
        for entry in ranges:
            if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                continue
            try:
                windows[index].append(
                    OpeningWindow(_parse_clock(entry[0]), _parse_clock(entry[1]))
                )
            except (ValueError, TypeError, AttributeError):
                continue
    return windows


def _windows_covering_day(
    hours: dict[int, list[OpeningWindow]], day: date
) -> list[tuple[datetime, datetime]]:
    """Aware start/end datetimes covering one calendar day.

    Includes any overnight shift that started the previous day, so a café open
    until 01:00 on Saturday reads as open at 00:30 on Saturday.
    """
    spans: list[tuple[datetime, datetime]] = []
    for window in hours[day.weekday()]:
        opens = _in_site_timezone(datetime.combine(day, window.opens))
        closes = _in_site_timezone(datetime.combine(day, window.closes))
        if window.spans_midnight:
            closes += timedelta(days=1)
        spans.append((opens, closes))

    # Pull in overnight shifts that started yesterday.
    previous_day = day - timedelta(days=1)
    for window in hours[previous_day.weekday()]:
        if not window.spans_midnight:
            continue
        opens = _in_site_timezone(datetime.combine(previous_day, window.opens))
        closes = _in_site_timezone(datetime.combine(previous_day, window.closes))
        closes += timedelta(days=1)
        spans.append((opens, closes))

    spans.sort()
    return spans


def is_open_at(raw_hours: object, moment: datetime) -> bool:
    hours = parse_opening_hours(raw_hours)
    probe = _in_site_timezone(_wall_clock(moment))
    return any(
        opens <= probe < closes
        for opens, closes in _windows_covering_day(hours, probe.date())
    )


def open_state_at(
    raw_hours: object,
    moment: datetime,
    closing_soon_minutes: int = CLOSING_SOON_MINUTES,
) -> OpenState:
    hours = parse_opening_hours(raw_hours)
    probe = _in_site_timezone(_wall_clock(moment))

    for opens, closes in _windows_covering_day(hours, probe.date()):
        if opens <= probe < closes:
            if closes - probe <= timedelta(minutes=closing_soon_minutes):
                return CLOSING_SOON
            return OPEN
    return CLOSED


def next_closing_at(raw_hours: object, moment: datetime) -> datetime | None:
    """The next moment the café stops serving, if it is currently open.

    The returned datetime is timezone aware so it can be compared directly with
    arrival and ready-by times.
    """
    hours = parse_opening_hours(raw_hours)
    probe = _in_site_timezone(_wall_clock(moment))

    for offset in range(0, 8):
        day = probe.date() + timedelta(days=offset)
        for opens, closes in _windows_covering_day(hours, day):
            if opens <= probe < closes:
                return closes
    return None


def format_hours_summary(raw_hours: object) -> str:
    """One-line summary such as ``Mon–Fri 07:00–18:00, Sat 08:00–18:00``."""
    hours = parse_opening_hours(raw_hours)
    if not any(hours.values()):
        return "Hours not set"

    parts: list[str] = []
    for index in range(7):
        windows = hours[index]
        if not windows:
            continue
        rendered = ", ".join(
            f"{window.opens.strftime('%H:%M')}–{window.closes.strftime('%H:%M')}"
            for window in windows
        )
        parts.append(f"{DAY_KEYS[index].capitalize()} {rendered}")

    if len(parts) > 3:
        return f"{parts[0]} – {parts[-1]} and {len(parts) - 2} more days"
    return "; ".join(parts)