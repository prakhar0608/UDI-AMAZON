from datetime import datetime, timezone

from amazon_ads_app.date_windows import last_n_calendar_days_in_zone


def test_last_n_calendar_days_in_zone_can_shift_vs_utc_day():
    now_utc = datetime(2026, 4, 7, 20, 0, tzinfo=timezone.utc)
    # At 20:00 UTC on April 7, it's already April 8 01:30 in IST.
    # We now end at yesterday relative to IST, which is April 7.
    start, end, dates = last_n_calendar_days_in_zone("Asia/Kolkata", 2, now=now_utc)
    assert end == "2026-04-07"
    assert start == "2026-04-06"
    assert dates == ["2026-04-06", "2026-04-07"]
