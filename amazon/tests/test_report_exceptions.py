from amazon_ads_app.reports_v3 import ReportPollTimeout


def test_report_poll_timeout_fields():
    e = ReportPollTimeout("rid-1", "/tmp/raw", elapsed_seconds=100.0, max_minutes=25.0)
    assert e.report_id == "rid-1"
    assert e.raw_dir == "/tmp/raw"
    assert "rid-1" in str(e)
