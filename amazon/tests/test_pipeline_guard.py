import pytest

from amazon_ads_app.config import AppConfig, ProfileConfig
from amazon_ads_app.pipeline import run_profile


def test_run_profile_rejects_invalid_id(monkeypatch, tmp_path):
    app = AppConfig(
        lwa_client_id="a",
        lwa_client_secret="b",
        lwa_refresh_token="c",
        profiles_path=tmp_path / "p.yaml",
        project_root=tmp_path,
    )
    prof = ProfileConfig(id=-1, region="NA", display_name="X")
    with pytest.raises(ValueError, match="profile id"):
        run_profile(app, prof)


def test_resume_requires_raw_dir(monkeypatch, tmp_path):
    app = AppConfig(
        lwa_client_id="a",
        lwa_client_secret="b",
        lwa_refresh_token="c",
        profiles_path=tmp_path / "p.yaml",
        project_root=tmp_path,
    )
    prof = ProfileConfig(id=1, region="NA", display_name="X")
    with pytest.raises(ValueError, match="resume_raw_dir"):
        run_profile(app, prof, resume_report_id="rid")
