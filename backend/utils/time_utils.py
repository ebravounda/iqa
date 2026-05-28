"""Time / timezone helpers for occupancy and daily-rollover queries.

Background: timestamps in MongoDB are stored as ISO strings in UTC.
However, gyms operate on local calendar days (Europe/Madrid by default in
Spain). If we compute "today_start" naively in UTC, then after 00:00 UTC
(which is 01:00 or 02:00 local time in Spain depending on DST), members
who entered yesterday but are still inside the gym disappear from the
occupancy counter. This module fixes that by computing "today_start" in
the gym's local timezone and then converting it back to UTC for the
Mongo range query.
"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

DEFAULT_TZ = "Europe/Madrid"


def _resolve_tz(tz_input):
    """Accept a tz string or a gym dict. Falls back to DEFAULT_TZ."""
    if isinstance(tz_input, dict):
        tz_str = tz_input.get("timezone") or DEFAULT_TZ
    else:
        tz_str = tz_input or DEFAULT_TZ
    try:
        return ZoneInfo(tz_str)
    except Exception:
        return ZoneInfo(DEFAULT_TZ)


def get_today_start_utc(tz_input=None) -> datetime:
    """Returns the UTC datetime corresponding to 00:00 of today in the
    gym's local timezone. Use the .isoformat() for Mongo range queries.
    """
    tz = _resolve_tz(tz_input)
    now_local = datetime.now(tz)
    local_midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight.astimezone(timezone.utc)


def get_month_start_utc(tz_input=None) -> datetime:
    tz = _resolve_tz(tz_input)
    now_local = datetime.now(tz)
    local_month_start = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return local_month_start.astimezone(timezone.utc)


def get_week_start_utc(tz_input=None) -> datetime:
    tz = _resolve_tz(tz_input)
    now_local = datetime.now(tz)
    local_today = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    local_week_start = local_today - timedelta(days=local_today.weekday())
    return local_week_start.astimezone(timezone.utc)
