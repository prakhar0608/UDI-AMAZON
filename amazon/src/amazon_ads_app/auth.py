"""Login with Amazon token refresh with in-memory cache."""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from dataclasses import dataclass

import httpx

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"

logger = logging.getLogger(__name__)


def _debug_auth_enabled() -> bool:
    return os.environ.get("AMAZON_ADS_DEBUG_AUTH", "").strip().lower() in ("1", "true", "yes")


def token_fingerprint(token: str) -> dict[str, int | str]:
    """Safe diagnostic: length + first 8 hex chars of SHA-256 (never log raw token)."""
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return {"len": len(token), "sha256_prefix": digest[:8]}


def validate_bearer_token_string(token: str) -> str:
    """
    Normalize and validate OAuth access token string for Authorization: Bearer …
    """
    s = str(token).strip()
    if not s:
        raise ValueError("Access token is empty after stripping.")
    if not s.isascii() or not s.isprintable():
        raise ValueError(
            "Access token contains non-ASCII or non-printable characters; "
            "check LWA response or environment variables."
        )
    if any(c.isspace() for c in s):
        raise ValueError(
            "Access token contains whitespace or newlines; fix LWA refresh response or `.env`. "
            "Tokens must be a single contiguous string."
        )
    if len(s) < 16:
        raise ValueError("Access token looks too short; LWA response may be malformed.")
    if len(s) >= 6 and s[:6].lower() == "bearer":
        raise ValueError(
            "Access token must not include a 'Bearer' prefix; it is added by the client. "
            "Paste only the token string from LWA, not the full Authorization header."
        )
    return s


@dataclass
class CachedToken:
    access_token: str
    expires_at: float  # monotonic-unrelated: use time.time() + expires_in - skew


class LwaTokenProvider:
    """Refresh OAuth access tokens using a refresh token."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        *,
        skew_seconds: float = 300,
        timeout: float = 30.0,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._skew = skew_seconds
        self._timeout = timeout
        self._lock = threading.Lock()
        self._cached: CachedToken | None = None

    def get_access_token(self) -> str:
        with self._lock:
            now = time.time()
            if self._cached and now < self._cached.expires_at - self._skew:
                return self._cached.access_token
            token = self._refresh()
            self._cached = token
            return token.access_token

    def _refresh(self) -> CachedToken:
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(
                LWA_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": self._client_id.strip(),
                    "client_secret": self._client_secret.strip(),
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "AmazonAdsApp/0.1.0",
                    "Accept": "application/json",
                },
            )
            r.raise_for_status()
            body = r.json()
        access = validate_bearer_token_string(body["access_token"])
        expires_in = float(body.get("expires_in", 3600))
        if _debug_auth_enabled():
            fp = token_fingerprint(access)
            logger.info(
                "lwa_token_refreshed",
                extra={
                    "expires_in": int(expires_in),
                    "token_len": fp["len"],
                    "token_sha256_prefix": fp["sha256_prefix"],
                },
            )
        return CachedToken(access_token=access, expires_at=time.time() + expires_in)
