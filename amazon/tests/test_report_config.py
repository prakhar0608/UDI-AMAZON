from unittest.mock import patch

from amazon_ads_app.report_config import compute_poll_interval_seconds


def test_poll_interval_stages_no_jitter():
    with patch("amazon_ads_app.report_config.random.uniform", return_value=0.0):
        # Under 30 attempts, poll interval is fixed to 5.0
        assert compute_poll_interval_seconds(0) == 5.0
        assert compute_poll_interval_seconds(1) == 5.0
        assert compute_poll_interval_seconds(29) == 5.0
        # For 30 and beyond, it transitions to 15.0 + (attempt_index - 30) % 10
        assert compute_poll_interval_seconds(30) == 15.0
        assert compute_poll_interval_seconds(31) == 16.0
        assert compute_poll_interval_seconds(39) == 24.0
        assert compute_poll_interval_seconds(40) == 15.0
