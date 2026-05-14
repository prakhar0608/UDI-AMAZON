from types import SimpleNamespace

import pandas as pd

from amazon_ads_app.config import AppConfig, ProfileConfig
from amazon_ads_app.parse_report import ParseReportResult
from amazon_ads_app.pipeline import run_profile


def _app(tmp_path):
    return AppConfig(
        lwa_client_id="cid",
        lwa_client_secret="sec",
        lwa_refresh_token="ref",
        profiles_path=tmp_path / "profiles.yaml",
        project_root=tmp_path,
    )


def test_run_profile_infers_daily_when_date_missing(tmp_path, monkeypatch):
    app = _app(tmp_path)
    prof = ProfileConfig(
        id=1,
        region="EU",
        display_name="Account",
        timezone="Asia/Kolkata",
        currency_code="INR",
    )
    monkeypatch.setattr("amazon_ads_app.pipeline.safe_last_n_days", lambda n, zone: ("2026-04-03", "2026-04-07", [f"2026-04-0{i}" for i in range(3, 8)], "Asia/Kolkata"))
    monkeypatch.setattr(
        "amazon_ads_app.pipeline.run_report_pipeline",
        lambda *args, **kwargs: SimpleNamespace(payload_bytes=b"[]", raw_dir=str(tmp_path)),
    )
    missing_date_df = pd.DataFrame(
        [
            {"campaign_id": "1", "campaign_name": "A", "date": "", "spend": 1.0, "sales": 10.0},
            {"campaign_id": "1", "campaign_name": "A", "date": "", "spend": 2.0, "sales": 20.0},
            {"campaign_id": "1", "campaign_name": "A", "date": "", "spend": 3.0, "sales": 30.0},
            {"campaign_id": "1", "campaign_name": "A", "date": "", "spend": 4.0, "sales": 40.0},
            {"campaign_id": "1", "campaign_name": "A", "date": "", "spend": 5.0, "sales": 50.0},
        ]
    )
    monkeypatch.setattr(
        "amazon_ads_app.pipeline.parse_report_payload_with_meta",
        lambda _: ParseReportResult(dataframe=missing_date_df, has_row_date=False),
    )

    res = run_profile(app, prof)
    assert res.used_missing_date_fallback is True
    assert "spend_2026-04-03" in res.wide.columns
    assert float(res.wide.loc[0, "spend_2026-04-03"]) == 1.0
    assert float(res.wide.loc[0, "spend_2026-04-07"]) == 5.0


def test_run_profile_keeps_daily_path_when_date_present(tmp_path, monkeypatch):
    app = _app(tmp_path)
    prof = ProfileConfig(id=1, region="EU", display_name="Account")
    monkeypatch.setattr(
        "amazon_ads_app.pipeline.safe_last_n_days",
        lambda n, zone: ("2026-04-03", "2026-04-07", [f"2026-04-0{i}" for i in range(3, 8)], "UTC"),
    )
    monkeypatch.setattr(
        "amazon_ads_app.pipeline.run_report_pipeline",
        lambda *args, **kwargs: SimpleNamespace(payload_bytes=b"[]", raw_dir=str(tmp_path)),
    )
    daily_df = pd.DataFrame(
        [
            {"campaign_id": "1", "campaign_name": "A", "date": "2026-04-03", "spend": 10.0, "sales": 50.0},
        ]
    )
    monkeypatch.setattr(
        "amazon_ads_app.pipeline.parse_report_payload_with_meta",
        lambda _: ParseReportResult(dataframe=daily_df, has_row_date=True),
    )

    res = run_profile(app, prof)
    assert res.used_missing_date_fallback is False
    assert "spend_2026-04-03" in res.wide.columns
