from pathlib import Path

from amazon_ads_app.config import ProfileConfig
from amazon_ads_app.profile_cache import (
    CachedProfiles,
    load_cache,
    profiles_from_jsonable,
    profiles_to_jsonable,
    save_cache,
)


def test_cache_round_trip(tmp_path: Path):
    p = tmp_path / "profiles_cache.json"
    profs = [
        ProfileConfig(id=1, region="NA", display_name="A"),
        ProfileConfig(id=2, region="EU", display_name="B"),
    ]
    c = CachedProfiles(fetched_at="2026-04-07T00:00:00+00:00", profiles=profs, errors={"FE": "fail"})
    save_cache(p, c)
    loaded = load_cache(p)
    assert loaded is not None
    assert loaded.fetched_at == c.fetched_at
    assert len(loaded.profiles) == 2
    assert loaded.profiles[0].id == 1
    assert loaded.errors["FE"] == "fail"


def test_profiles_to_jsonable():
    profs = [ProfileConfig(id=99, region="FE", display_name="X")]
    rows = profiles_to_jsonable(profs)
    assert rows == [
        {
            "id": 99,
            "region": "FE",
            "display_name": "X",
            "account_group": "",
            "timezone": None,
            "currency_code": None,
            "country_code": None,
        }
    ]


def test_profiles_from_jsonable_back_compat_missing_optional_fields():
    rows = [{"id": 3, "region": "EU", "display_name": "Legacy", "account_group": ""}]
    loaded = profiles_from_jsonable(rows)
    assert loaded[0].timezone is None
    assert loaded[0].currency_code is None
    assert loaded[0].country_code is None
