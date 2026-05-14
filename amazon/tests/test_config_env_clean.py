import pytest

from amazon_ads_app.config import _clean_env, load_app_config


def test_clean_env_strips_and_unquotes(monkeypatch):
    monkeypatch.setenv("TEST_LWA", '  "myclientid"  ')
    assert _clean_env("TEST_LWA") == "myclientid"


def test_clean_env_rejects_newline(monkeypatch):
    monkeypatch.setenv("TEST_LWA", "line1\nline2")
    with pytest.raises(ValueError, match="line break"):
        _clean_env("TEST_LWA")


def test_load_app_config_uses_clean_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LWA_CLIENT_ID", "cid")
    monkeypatch.setenv("LWA_CLIENT_SECRET", "sec")
    monkeypatch.setenv("LWA_REFRESH_TOKEN", "ref")
    cfg = load_app_config(env_path=tmp_path / "missing.env")
    assert cfg.lwa_client_id == "cid"
    assert cfg.lwa_refresh_token == "ref"
