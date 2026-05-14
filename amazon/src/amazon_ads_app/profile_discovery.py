"""Discover advertising profiles across NA / EU / FE using List Profiles API."""

from __future__ import annotations

import logging
from typing import Any

from amazon_ads_app.api_client import UnscopedAdsApiClient
from amazon_ads_app.auth import LwaTokenProvider
from amazon_ads_app.config import AppConfig, ProfileConfig
from amazon_ads_app.regions import REGION_HOSTS

logger = logging.getLogger(__name__)

LIST_PROFILES_PATH = "/v2/profiles"


def _account_group_from_row(row: dict[str, Any], profile_id: int) -> str:
    """
    Stable key so the same advertiser across regions groups together.
    Prefer account id; else normalized account name; else singleton per profile id.
    """
    acc = row.get("accountInfo")
    if isinstance(acc, dict):
        for key in ("id", "marketplaceStringId"):
            v = acc.get(key)
            if v is not None and str(v).strip():
                return f"id:{str(v).strip()}"
        name = acc.get("name")
        if name and str(name).strip():
            return f"name:{str(name).strip().lower()}"
    return f"pid:{profile_id}"


def _profile_row_to_display_name(row: dict[str, Any]) -> str:
    name = ""
    acc = row.get("accountInfo")
    if isinstance(acc, dict):
        name = str(acc.get("name") or acc.get("id") or "").strip()
    if not name:
        name = "Account"
    cc = row.get("countryCode") or ""
    cur = row.get("currencyCode") or ""
    bits = [name]
    if cc:
        bits.append(str(cc))
    if cur:
        bits.append(str(cur))
    return " — ".join(bits) if len(bits) > 1 else name


def _parse_profile_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("profiles", "data", "items"):
            v = payload.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []


def list_profiles_for_host(
    base_url: str,
    region_code: str,
    client_id: str,
    token_provider: LwaTokenProvider,
    *,
    timeout: float = 60.0,
) -> tuple[list[ProfileConfig], str | None]:
    """
    GET List Profiles for one regional host.
    Returns (profiles, error_message). error_message is None on HTTP success.
    """
    with UnscopedAdsApiClient(base_url, client_id, token_provider, timeout=timeout) as client:
        try:
            r = client.request("GET", LIST_PROFILES_PATH)
            if r.status_code >= 400:
                msg = f"HTTP {r.status_code}: {r.text[:500]}"
                logger.warning("list_profiles_failed", extra={"region": region_code, "detail": msg})
                return [], msg
            data = r.json()
        except Exception as e:
            msg = str(e)
            logger.exception("list_profiles_exception", extra={"region": region_code})
            return [], msg

    rows = _parse_profile_payload(data)
    out: list[ProfileConfig] = []
    for row in rows:
        pid = row.get("profileId")
        if pid is None:
            continue
        try:
            pid_int = int(pid)
        except (TypeError, ValueError):
            continue
        display = _profile_row_to_display_name(row)
        ag = _account_group_from_row(row, pid_int)
        out.append(
            ProfileConfig(
                id=pid_int,
                region=region_code.upper().strip(),
                display_name=display,
                account_group=ag,
                timezone=(str(row.get("timezone")).strip() or None) if row.get("timezone") else None,
                currency_code=(
                    str(row.get("currencyCode")).strip() or None
                )
                if row.get("currencyCode")
                else None,
                country_code=(str(row.get("countryCode")).strip() or None)
                if row.get("countryCode")
                else None,
            )
        )
    return out, None


def discover_all_profiles(
    app: AppConfig,
    token_provider: LwaTokenProvider | None = None,
) -> tuple[list[ProfileConfig], dict[str, str]]:
    """
    Query each regional host, merge profiles, dedupe by profile id (first wins).
    Returns (profiles, region_errors) where region_errors maps region code -> message for failed hosts.
    """
    tp = token_provider or LwaTokenProvider(
        app.lwa_client_id,
        app.lwa_client_secret,
        app.lwa_refresh_token,
    )
    merged: dict[int, ProfileConfig] = {}
    region_errors: dict[str, str] = {}

    for region_code, base_url in REGION_HOSTS.items():
        profiles, err = list_profiles_for_host(
            base_url,
            region_code,
            app.lwa_client_id,
            tp,
        )
        if err:
            region_errors[region_code] = err
        for p in profiles:
            if p.id not in merged:
                merged[p.id] = p

    return list(merged.values()), region_errors


def resolve_profile(app: AppConfig, profile_id: int) -> ProfileConfig | None:
    """Resolve a profile by id from manual YAML (if present) then from discovery cache."""
    from amazon_ads_app.config import load_profiles
    from amazon_ads_app.profile_cache import default_cache_path, load_cache

    if app.profiles_path.exists():
        for p in load_profiles(app.profiles_path):
            if p.id == profile_id:
                return p
    cached = load_cache(default_cache_path(app.project_root))
    if cached:
        for p in cached.profiles:
            if p.id == profile_id:
                return p
    return None
