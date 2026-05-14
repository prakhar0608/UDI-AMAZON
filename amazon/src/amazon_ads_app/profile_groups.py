"""Group advertising profiles by account (multi-region) and filter for UI."""

from __future__ import annotations

from collections import defaultdict

from amazon_ads_app.config import ProfileConfig


def _effective_group_key(p: ProfileConfig) -> str:
    if p.account_group.strip():
        return p.account_group.strip()
    return f"__single:{p.id}"


def group_profiles_by_account(profiles: list[ProfileConfig]) -> dict[str, list[ProfileConfig]]:
    """Map group key -> profiles (sorted by region, then id)."""
    buckets: dict[str, list[ProfileConfig]] = defaultdict(list)
    for p in profiles:
        buckets[_effective_group_key(p)].append(p)
    for key in buckets:
        buckets[key].sort(key=lambda x: (x.region, x.id))
    return dict(buckets)


def filter_profiles_by_search(profiles: list[ProfileConfig], query: str) -> list[ProfileConfig]:
    """Case-insensitive match on display name, region, id, account group."""
    q = query.strip().lower()
    if not q:
        return list(profiles)
    out: list[ProfileConfig] = []
    for p in profiles:
        hay = " ".join(
            [
                p.display_name,
                p.region,
                str(p.id),
                p.account_group,
            ]
        ).lower()
        if q in hay:
            out.append(p)
    return out


def format_group_select_label(group_key: str, members: list[ProfileConfig]) -> str:
    """Short label for the account/group selectbox."""
    n = len(members)
    suffix = f" ({n} regions)" if n > 1 else ""
    if group_key.startswith("name:"):
        title = group_key[5:].strip() or "Account"
        return title.title() + suffix
    if group_key.startswith("id:"):
        return members[0].display_name + suffix if members else f"Account{suffix}"
    if group_key.startswith("pid:"):
        return members[0].display_name + suffix if members else f"Account{suffix}"
    if group_key.startswith("__single:"):
        return members[0].display_name + suffix if members else group_key
    return group_key + suffix
