"""Wall-clock timeout path for run_report_pipeline (resume mode, no HTTP)."""

from unittest.mock import MagicMock, patch

import pytest

from amazon_ads_app.reports_v3 import ReportPollTimeout, run_report_pipeline


def test_run_report_pipeline_raises_on_wall_clock_timeout(tmp_path):
    client = MagicMock()

    def fake_status(_client, _rid):
        return {"status": "PENDING"}

    # poll_t0=100; first loop elapsed=0; second loop elapsed=2100-100=2000s > 25*60
    monotonic_vals = [100.0, 100.0, 2100.0]

    def fake_monotonic():
        return monotonic_vals.pop(0)

    with (
        patch("amazon_ads_app.reports_v3.get_report_status", side_effect=fake_status),
        patch("amazon_ads_app.reports_v3.time.monotonic", side_effect=fake_monotonic),
        patch("amazon_ads_app.reports_v3.time.sleep"),
    ):
        with pytest.raises(ReportPollTimeout) as excinfo:
            run_report_pipeline(
                client,
                run_id="run1",
                start_date="2024-01-01",
                end_date="2024-01-05",
                raw_dir=str(tmp_path),
                resume_report_id="rep-timeout-1",
                max_poll_minutes=25.0,
            )
    assert excinfo.value.report_id == "rep-timeout-1"
    job = (tmp_path / "report_job.json").read_text(encoding="utf-8")
    assert "timeout" in job.lower() or "TIMEOUT" in job
