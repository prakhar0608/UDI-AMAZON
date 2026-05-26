"""Load environment variables and profile list."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


def _clean_env(name: str) -> str:
    """
    Read env var, strip whitespace, remove all surrounding quotes.
    Raises KeyError if missing, ValueError if empty or contains non-ASCII after cleanup.
    """
    raw = os.environ.get(name)
    if raw is None:
        raise KeyError(name)
    s = raw.strip()
    # Aggressively remove all surrounding quotes (e.g. "'token'" -> token)
    while len(s) >= 2 and (
        (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'"))
    ):
        s = s[1:-1].strip()
    if not s:
        raise ValueError(f"Environment variable {name} is empty after trimming/quotes.")
    if not s.isascii():
        raise ValueError(f"Environment variable {name} contains non-ASCII characters; fix `.env`.")
    if re.search(r"[\r\n]", s):
        raise ValueError(
            f"Environment variable {name} contains a line break; use a single-line value in `.env`."
        )
    return s


@dataclass(frozen=True)
class ProfileConfig:
    id: int
    region: str
    display_name: str
    #: Stable key to group the same logical account across regions (from API or YAML).
    account_group: str = ""
    timezone: str | None = None
    currency_code: str | None = None
    country_code: str | None = None


@dataclass(frozen=True)
class AppConfig:
    lwa_client_id: str
    lwa_client_secret: str
    lwa_refresh_token: str
    profiles_path: Path
    project_root: Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]
def load_app_config(
    env_path: Path | None = None,
    profiles_path: Path | None = None,
) -> AppConfig:
    root = _project_root()
    load_dotenv(env_path or root / ".env", override=True)

    def get_var(name: str) -> str:
        vite_name = f"VITE_{name}"
        if vite_name in os.environ:
            return _clean_env(vite_name)
        return _clean_env(name)

    return AppConfig(
        lwa_client_id=get_var("LWA_CLIENT_ID"),
        lwa_client_secret=get_var("LWA_CLIENT_SECRET"),
        lwa_refresh_token=get_var("LWA_REFRESH_TOKEN"),
        profiles_path=profiles_path or root / "config" / "profiles.yaml",
        project_root=root,
    )

def load_profiles(path: Path) -> list[ProfileConfig]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = raw.get("profiles") or []
    out: list[ProfileConfig] = []
    for row in items:
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
