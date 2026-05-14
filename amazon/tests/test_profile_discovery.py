from pathlib import Path
from unittest.mock import patch

from amazon_ads_app.config import AppConfig, ProfileConfig
from amazon_ads_app.profile_cache import default_cache_path, save_cache, build_cache_now
from amazon_ads_app.profile_discovery import discover_all_profiles, resolve_profile


def _app(tmp_path: Path) -> AppConfig:
    return AppConfig(
        lwa_client_id="cid",
        lwa_client_secret="sec",
        lwa_refresh_token="ref",
        profiles_path=tmp_path / "profiles.yaml",
        project_root=tmp_path,
    )


def test_discover_merges_and_dedupes(tmp_path: Path):
    app = _app(tmp_path)

    def fake_list2(base_url: str, region_code: str, client_id: str, token_provider, *, timeout: float = 60.0):
        if region_code == "NA":
            return ([ProfileConfig(id=1, region="NA", display_name="One")], None)
        if region_code == "EU":
            return ([ProfileConfig(id=1, region="EU", display_name="Dup")], None)
        return ([], None)

    with patch("amazon_ads_app.profile_discovery.list_profiles_for_host", side_effect=fake_list2):
        profiles, errors = discover_all_profiles(app)
    ids = {p.id for p in profiles}
    assert ids == {1}
    assert len(profiles) == 1
    assert profiles[0].display_name == "One"


def test_discover_collects_region_errors(tmp_path: Path):
    app = _app(tmp_path)

    def fake_list(base_url: str, region_code: str, client_id: str, token_provider, *, timeout: float = 60.0):
        if region_code == "NA":
            return ([ProfileConfig(id=10, region="NA", display_name="Ok")], None)
        return ([], f"HTTP 403 for {region_code}")

    with patch("amazon_ads_app.profile_discovery.list_profiles_for_host", side_effect=fake_list):
        profiles, errors = discover_all_profiles(app)
    assert len(profiles) == 1
    assert "EU" in errors and "FE" in errors


def test_resolve_profile_yaml_over_cache(tmp_path: Path):
    yaml_path = tmp_path / "profiles.yaml"
    yaml_path.write_text(
        "profiles:\n  - id: 5\n    region: NA\n    display_name: YAML\n",
        encoding="utf-8",
    )
    app = AppConfig(
        lwa_client_id="a",
        lwa_client_secret="b",
        lwa_refresh_token="c",
        profiles_path=yaml_path,
        project_root=tmp_path,
    )
    cache_path = default_cache_path(tmp_path)
    save_cache(
        cache_path,
        build_cache_now([ProfileConfig(id=5, region="EU", display_name="Cache")]),
    )
    r = resolve_profile(app, 5)
    assert r is not None
    assert r.region == "NA"
    assert r.display_name == "YAML"


def test_resolve_profile_from_cache_only(tmp_path: Path):
    app = _app(tmp_path)
    cache_path = default_cache_path(tmp_path)
    save_cache(
        cache_path,
        build_cache_now([ProfileConfig(id=7, region="FE", display_name="Cached")]),
    )
    r = resolve_profile(app, 7)
    assert r is not None
    assert r.id == 7
