import json
from pathlib import Path
from types import SimpleNamespace

from amazon_ads_app.config import AppConfig, ProfileConfig
from amazon_ads_app.pipeline import build_result_from_json_artifact, run_profile
from amazon_ads_app.date_windows import safe_last_n_days


def _app(tmp_path: Path) -> AppConfig:
    return AppConfig(
        lwa_client_id="cid",
        lwa_client_secret="sec",
        lwa_refresh_token="ref",
        profiles_path=tmp_path / "profiles.yaml",
        project_root=tmp_path,
    )


def test_build_result_from_json_artifact_uses_daily_rows(tmp_path: Path):
    app = _app(tmp_path)
    prof = ProfileConfig(id=1, region="EU", display_name="Account")
    raw = tmp_path / "data" / "raw" / "EU" / "Account" / "20260101T000000Z_aaaa"
    raw.mkdir(parents=True)
    fp = raw / "sp_campaigns_20260101T000000Z_aaaa.json"
    
    # Use actual safe dates to match the logic in build_result_from_json_artifact
    _, _, dates, _ = safe_last_n_days(5, prof.timezone)
    d1 = dates[0]
    d2 = dates[1]
    
    payload = [
        {"campaignId": 1, "campaignName": "A", "date": d1, "cost": 10, "sales1d": 50},
        {"campaignId": 1, "campaignName": "A", "date": d2, "cost": 11, "sales1d": 51},
    ]
    fp.write_text(json.dumps(payload), encoding="utf-8")

    res = build_result_from_json_artifact(app, prof, fp, days=5, run_id="cached")
    assert res.json_path == fp
    assert res.csv_name.endswith(".csv")
    assert f"spend_{d1}" in res.wide.columns


def test_run_profile_does_not_write_processed_files(tmp_path: Path, monkeypatch):
    app = _app(tmp_path)
    prof = ProfileConfig(id=1, region="EU", display_name="Account")
    raw = tmp_path / "data" / "raw" / "EU" / "Account" / "20260101T000000Z_aaaa"
    raw.mkdir(parents=True)
    json_path = raw / "sp_campaigns_20260101T000000Z_aaaa.json"
    
    _, _, dates, _ = safe_last_n_days(5, prof.timezone)
    d1 = dates[0]
    
    payload = [{"campaignId": 1, "campaignName": "A", "date": d1, "cost": 10, "sales1d": 50}]
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(
        "amazon_ads_app.pipeline.run_report_pipeline",
        lambda *args, **kwargs: SimpleNamespace(
            payload_bytes=b"[]",
            raw_dir=str(raw),
            extracted_json_path=str(json_path),
        ),
    )
    res = run_profile(app, prof)
    assert res.json_path == json_path
    assert not (tmp_path / "data" / "processed").exists()
