"""Map logical region codes to Amazon Advertising API base URLs."""

from __future__ import annotations

from typing import Final

# Per Amazon Ads API documentation — verify in your integration guide if requests fail.
REGION_HOSTS: Final[dict[str, str]] = {
    "NA": "https://advertising-api.amazon.com",
    "EU": "https://advertising-api-eu.amazon.com",
    "FE": "https://advertising-api-fe.amazon.com",
}


def base_url_for_region(region: str) -> str:
    r = region.upper().strip()
    if r not in REGION_HOSTS:
        raise ValueError(f"Unknown region {region!r}. Expected one of {sorted(REGION_HOSTS)}")
    return REGION_HOSTS[r]
