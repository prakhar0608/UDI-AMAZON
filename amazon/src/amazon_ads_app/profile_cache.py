"""On-disk cache for discovered profiles (under data/cache/)."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from amazon_ads_app.config import ProfileConfig

CACHE_FILENAME = "profiles_cache.json"


def default_cache_path(project_root: Path) -> Path:
    return project_root / "data" / "cache" / CACHE_FILENAME


def profiles_to_jsonable(profiles: list[ProfileConfig]) -> list[dict[str, Any]]:
    return [asdict(p) for p in profiles]


def profiles_from_jsonable(rows: list[dict[str, Any]]) -> list[ProfileConfig]:
    out: list[ProfileConfig] = []
    for row in rows:
        out.append(
            ProfileConfig(
                id=int(row["id"]),
                region=str(row["region"]),
                display_name=str(row["display_name"]),
                account_group=str(row.get("account_group") or ""),
                timezone=(str(row.get("timezone")).strip() or None) if row.get("timezone") else None,
                currency_code=(
                    str(row.get("currency_code")).strip() or None
                )
                if row.get("currency_code")
                else None,
                country_code=(str(row.get("country_code")).strip() or None)
                if row.get("country_code")
                else None,
            )
        )
    return out


class CachedProfiles:
    def __init__(
        self,
        fetched_at: str,
        profiles: list[ProfileConfig],
        errors: dict[str, str] | None = None,
    ) -> None:
        self.fetched_at = fetched_at
        self.profiles = profiles
        self.errors = errors or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "fetched_at": self.fetched_at,
            "profiles": profiles_to_jsonable(self.profiles),
            "errors": dict(self.errors),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CachedProfiles:
        rows = data.get("profiles") or []
        profs = profiles_from_jsonable(rows) if rows else []
        err = data.get("errors") or {}
        fa = str(data.get("fetched_at") or datetime.now(timezone.utc).isoformat())
        return cls(fetched_at=fa, profiles=profs, errors=err if isinstance(err, dict) else {})


def load_cache(path: Path) -> CachedProfiles | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return CachedProfiles.from_dict(data)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def save_cache(path: Path, cached: CachedProfiles) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cached.to_dict(), indent=2), encoding="utf-8")


def cache_is_stale(fetched_at_iso: str, ttl_seconds: float) -> bool:
    """Return True if older than ttl_seconds (or unparseable)."""
    try:
        # Support Z suffix
        ts = fetched_at_iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - dt).total_seconds() > ttl_seconds
    except (ValueError, TypeError):
        return True


def build_cache_now(
    profiles: list[ProfileConfig],
    errors: dict[str, str] | None = None,
) -> CachedProfiles:
    return CachedProfiles(
        fetched_at=datetime.now(timezone.utc).isoformat(),
        profiles=profiles,
        errors=errors or {},
    )
