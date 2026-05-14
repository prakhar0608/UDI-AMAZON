from unittest.mock import patch

from amazon_ads_app.report_config import compute_poll_interval_seconds


def test_poll_interval_stages_no_jitter():
    with patch("amazon_ads_app.report_config.random.uniform", return_value=0.0):
        assert compute_poll_interval_seconds(0) == 5.0
        assert compute_poll_interval_seconds(1) == 8.0
        assert compute_poll_interval_seconds(2) == 12.0
        assert compute_poll_interval_seconds(3) == 20.0
        assert compute_poll_interval_seconds(4) == 25.0
        assert compute_poll_interval_seconds(5) == 30.0
        assert compute_poll_interval_seconds(6) == 45.0
        assert compute_poll_interval_seconds(7) == 46.0
