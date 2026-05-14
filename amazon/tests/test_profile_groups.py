from amazon_ads_app.config import ProfileConfig
from amazon_ads_app.profile_groups import (
    filter_profiles_by_search,
    format_group_select_label,
    group_profiles_by_account,
)


def test_group_by_account_name():
    profiles = [
        ProfileConfig(1, "NA", "A — US", account_group="name:acme"),
        ProfileConfig(2, "EU", "A — UK", account_group="name:acme"),
        ProfileConfig(3, "FE", "Other", account_group="name:other"),
    ]
    g = group_profiles_by_account(profiles)
    assert len(g["name:acme"]) == 2
    assert len(g["name:other"]) == 1


def test_single_profile_without_group_key():
    profiles = [ProfileConfig(10, "NA", "Solo", account_group="")]
    g = group_profiles_by_account(profiles)
    assert len(g) == 1
    assert g["__single:10"][0].id == 10


def test_filter_search():
    profiles = [
        ProfileConfig(1, "NA", "Alpha", account_group=""),
        ProfileConfig(2, "EU", "Beta", account_group=""),
    ]
    assert len(filter_profiles_by_search(profiles, "eu")) == 1
    assert len(filter_profiles_by_search(profiles, "2")) == 1


def test_format_group_label():
    members = [ProfileConfig(1, "NA", "x", account_group="name:acme")]
    assert "Acme" in format_group_select_label("name:acme", members)
