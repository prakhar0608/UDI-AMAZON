"""Lightweight API checks before running heavy report jobs."""

from __future__ import annotations

from typing import Any

from amazon_ads_app.api_client import AdsApiClient, UnscopedAdsApiClient
from amazon_ads_app.auth import LwaTokenProvider, token_fingerprint
from amazon_ads_app.config import AppConfig, ProfileConfig
from amazon_ads_app.regions import REGION_HOSTS, base_url_for_region

LIST_PROFILES_PATH = "/v2/profiles"


def validate_unscoped_region(
    app: AppConfig,
    region_code: str,
    token_provider: LwaTokenProvider,
) -> tuple[bool, str]:
    """GET List Profiles without scope. Returns (ok, detail)."""
    base = base_url_for_region(region_code)
    try:
        with UnscopedAdsApiClient(base, app.lwa_client_id, token_provider) as client:
            r = client.request("GET", LIST_PROFILES_PATH)
            if r.status_code == 200:
                return True, "OK"
            return False, f"HTTP {r.status_code}: {r.text[:400]}"
    except Exception as e:
        return False, str(e)


def validate_all_regions_unscoped(
    app: AppConfig,
    token_provider: LwaTokenProvider | None = None,
) -> dict[str, tuple[bool, str]]:
    """Run unscoped list-profiles against NA, EU, FE."""
    tp = token_provider or LwaTokenProvider(
        app.lwa_client_id,
        app.lwa_client_secret,
        app.lwa_refresh_token,
    )
    out: dict[str, tuple[bool, str]] = {}
    for region_code in REGION_HOSTS:
        ok, msg = validate_unscoped_region(app, region_code, tp)
        out[region_code] = (ok, msg)
    return out


def validate_scoped_profile(
    app: AppConfig,
    profile: ProfileConfig,
    token_provider: LwaTokenProvider | None = None,
) -> tuple[bool, str]:
    """
    Call GET /v2/profiles with Amazon-Advertising-API-Scope set (same as reporting).
    """
    tp = token_provider or LwaTokenProvider(
        app.lwa_client_id,
        app.lwa_client_secret,
        app.lwa_refresh_token,
    )
    base = base_url_for_region(profile.region)
    try:
        with AdsApiClient(
            base,
            app.lwa_client_id,
            tp,
            profile_id=profile.id,
        ) as client:
            r = client.request("GET", LIST_PROFILES_PATH)
            if r.status_code == 200:
                return True, "OK"
            return False, f"HTTP {r.status_code}: {r.text[:400]}"
    except Exception as e:
        return False, str(e)


def auth_debug_info(app: AppConfig, token_provider: LwaTokenProvider | None = None) -> dict[str, Any]:
    """Safe fingerprint of current access token (after refresh if needed)."""
    tp = token_provider or LwaTokenProvider(
        app.lwa_client_id,
        app.lwa_client_secret,
        app.lwa_refresh_token,
    )
    tok = tp.get_access_token()
    fp = token_fingerprint(tok)
    return {"token_len": fp["len"], "token_sha256_prefix": fp["sha256_prefix"]}
