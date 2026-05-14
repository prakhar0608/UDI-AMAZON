"""Date window helpers for report requests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def last_n_calendar_days_utc(n: int = 5) -> tuple[str, str, list[str]]:
    """Return (start_iso, end_iso, ordered date strings) in UTC dates, ending yesterday."""
    end = datetime.now(timezone.utc).date() - timedelta(days=1)
    start = end - timedelta(days=n - 1)
    dates: list[str] = []
    cur = start
    while cur <= end:
        dates.append(cur.isoformat())
        cur += timedelta(days=1)
    return start.isoformat(), end.isoformat(), dates


def last_n_calendar_days_in_zone(
    zone_name: str,
    n: int = 5,
    now: datetime | None = None,
) -> tuple[str, str, list[str]]:
    """Return (start_iso, end_iso, ordered date strings) in the requested timezone, ending yesterday."""
    z = ZoneInfo(zone_name)
    ref = now or datetime.now(timezone.utc)
    # end_at_today would be ref.astimezone(z).date()
    # we want yesterday
    end = ref.astimezone(z).date() - timedelta(days=1)
    start = end - timedelta(days=n - 1)
    dates: list[str] = []
    cur = start
    while cur <= end:
        dates.append(cur.isoformat())
        cur += timedelta(days=1)
    return start.isoformat(), end.isoformat(), dates


def safe_last_n_days(
    n: int,
    zone_name: str | None,
) -> tuple[str, str, list[str], str]:
    """Return window and label; gracefully fallback to UTC."""
    if zone_name:
        try:
            start, end, dates = last_n_calendar_days_in_zone(zone_name, n)
            return start, end, dates, zone_name
        except (ZoneInfoNotFoundError, ValueError):
            pass
    start, end, dates = last_n_calendar_days_utc(n)
    return start, end, dates, "UTC"


def last_n_days_till_yesterday(n: int, zone_name: str = "Asia/Kolkata") -> tuple[str, str, list[str]]:
    """Return window for last N days, ending yesterday."""
    z = ZoneInfo(zone_name)
    yesterday = datetime.now(z).date() - timedelta(days=1)
    start = yesterday - timedelta(days=n - 1)
    dates: list[str] = []
    cur = start
    while cur <= yesterday:
        dates.append(cur.isoformat())
        cur += timedelta(days=1)
    return start.isoformat(), yesterday.isoformat(), dates


def mtd_till_yesterday(zone_name: str = "Asia/Kolkata") -> tuple[str, str, list[str]]:
    """Return window for Month-To-Date, ending yesterday."""
    z = ZoneInfo(zone_name)
    now = datetime.now(z).date()
    yesterday = now - timedelta(days=1)
    
    # If today is the 1st, MTD till yesterday might mean nothing or last month.
    # Usually MTD till yesterday is only valid from the 2nd onwards.
    # If today is the 1st, we return just yesterday (last day of prev month).
    start = yesterday.replace(day=1)
    
    dates: list[str] = []
    cur = start
    while cur <= yesterday:
        dates.append(cur.isoformat())
        cur += timedelta(days=1)
    return start.isoformat(), yesterday.isoformat(), dates
