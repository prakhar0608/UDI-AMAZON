"""Authenticated HTTP client for Amazon Advertising API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from amazon_ads_app.auth import LwaTokenProvider, token_fingerprint, validate_bearer_token_string

logger = logging.getLogger(__name__)


class AdsApiClient:
    def __init__(
        self,
        base_url: str,
        client_id: str,
        token_provider: LwaTokenProvider,
        *,
        profile_id: int,
        timeout: float = 120.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._client_id = str(client_id).strip()
        self._tokens = token_provider
        self._profile_id = str(profile_id).strip()
        self._timeout = timeout
        self._client = httpx.Client(timeout=self._timeout, http2=True)

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        token = self._tokens.get_access_token()
        # The space after Bearer must be exactly one ASCII space.
        h = {
            "Authorization": f"Bearer {token}",
            "Amazon-Advertising-API-ClientId": self._client_id,
            "Amazon-Advertising-API-Scope": self._profile_id,
        }
        if extra:
            h.update(extra)
        return h

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = f"{self._base}{path}"
        merged = self._headers(headers)
        r = self._client.request(method, url, json=json, headers=merged)
        if r.status_code == 403:
            fp = token_fingerprint(merged["Authorization"][7:])
            logger.warning(
                "request_403_forbidden",
                extra={
                    "url": url,
                    "profile_id": self._profile_id,
                    "token_len": fp["len"],
                    "token_sha256_prefix": fp["sha256_prefix"],
                    "response_body": r.text[:500],
                },
            )
        return r

    def __enter__(self) -> AdsApiClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self._client.close()


class UnscopedAdsApiClient:
    def __init__(
        self,
        base_url: str,
        client_id: str,
        token_provider: LwaTokenProvider,
        *,
        timeout: float = 60.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._client_id = str(client_id).strip()
        self._tokens = token_provider
        self._timeout = timeout
        self._client = httpx.Client(timeout=self._timeout)

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        token = self._tokens.get_access_token()
        h = {
            "Authorization": f"Bearer {token}",
            "Amazon-Advertising-API-ClientId": self._client_id,
        }
        if extra:
            h.update(extra)
        return h

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = f"{self._base}{path}"
        merged = self._headers(headers)
        r = self._client.request(method, url, json=json, headers=merged)
        if r.status_code == 403:
            fp = token_fingerprint(merged["Authorization"][7:])
            logger.warning(
                "unscoped_request_403_forbidden",
                extra={
                    "url": url,
                    "token_len": fp["len"],
                    "token_sha256_prefix": fp["sha256_prefix"],
                    "response_body": r.text[:500],
                },
            )
        return r

    def __enter__(self) -> UnscopedAdsApiClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self._client.close()
