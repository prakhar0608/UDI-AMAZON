"""Amazon Ads Reporting API v3: create report, poll, download."""

from __future__ import annotations

import gzip
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

import httpx

from amazon_ads_app.api_client import AdsApiClient
from amazon_ads_app.report_config import (
    CREATE_RETRY_ATTEMPTS,
    MAX_POLL_ATTEMPTS_SAFETY,
    MAX_POLL_MINUTES,
    compute_poll_interval_seconds,
)

logger = logging.getLogger(__name__)

# Standard V3 path. 
REPORTING_PREFIXES = ("/reporting",)
CONTENT_CREATE = "application/vnd.createasyncreportrequest.v3+json"
CONTENT_REPORT = "application/vnd.createasyncreportresponse.v3+json"


ProgressCallback = Callable[[str, str], None]


def _noop_progress(step: str, detail: str) -> None:
    pass


class ReportPollTimeout(RuntimeError):
    """Raised when a report stays pending longer than max_poll_minutes."""

    def __init__(
        self,
        report_id: str,
        raw_dir: str,
        *,
        elapsed_seconds: float,
        max_minutes: float,
    ) -> None:
        self.report_id = report_id
        self.raw_dir = raw_dir
        self.elapsed_seconds = elapsed_seconds
        self.max_minutes = max_minutes
        super().__init__(
            f"Report {report_id} still pending after {elapsed_seconds:.0f}s "
            f"(limit {max_minutes:g} min). Use Resume polling with the same report id."
        )


@dataclass(frozen=True)
class ReportArtifacts:
    report_id: str
    raw_dir: str
    downloaded_path: str
    extracted_json_path: str
    payload_bytes: bytes


def _cooldown_from_response(status_code: int, body: str) -> float:
    if status_code == 429:
        return 60.0
    if "Quota exceeded" in body or "throttl" in body.lower():
        return 45.0
    return 15.0


def _job_path(raw_dir: str) -> str:
    return os.path.join(raw_dir, "report_job.json")


def _write_report_job(
    raw_dir: str,
    *,
    run_id: str,
    report_id: str,
    start_date: str,
    end_date: str,
    state: str,
    attempt_count: int = 0,
    last_status: str | None = None,
) -> None:
    os.makedirs(raw_dir, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "runId": run_id,
        "reportId": report_id,
        "startDate": start_date,
        "endDate": end_date,
        "state": state,
        "attemptCount": attempt_count,
        "lastStatus": last_status,
        "lastPollAt": now,
        "updatedAt": now,
    }
    with open(_job_path(raw_dir), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def create_sp_daily_report(
    client: AdsApiClient,
    *,
    name: str,
    start_date: str,
    end_date: str,
    report_type: str = "spCampaigns",
    group_by: list[str] | None = None,
) -> str:
    if report_type == "spProducts":
        # For products, we group by 'advertiser' and request ad-level columns.
        group_by = ["advertiser"]
        v3_report_type_id = "spAdvertisedProduct"
        # Columns must include IDs since they are not in groupBy
        # Removed roasClicks14d, acosClicks14d as they are often invalid in V3
        columns = [
            "date", "adId", "advertisedAsin", "advertisedSku", "campaignId", "campaignName", "adGroupId", "adGroupName",
            "impressions", "clicks", "cost", "sales1d", "sales7d", "sales14d"
        ]
    elif report_type == "spAdGroups":
        # For adGroups, use 'spAdGroups' report type and group by adGroup
        group_by = ["adGroup"]
        v3_report_type_id = "spAdGroups"
        columns = [
            "date", "impressions", "clicks", "cost", "sales1d", "sales7d", "sales14d"
        ]
    elif report_type == "spTargeting":
        group_by = ["targeting"]
        v3_report_type_id = "spTargeting"
        columns = [
            "date", "impressions", "clicks", "cost", "sales1d", "sales7d", "sales14d"
        ]
    else:
        # Default to spCampaigns
        group_by = ["campaign"]
        v3_report_type_id = "spCampaigns"
        columns = [
            "date", "impressions", "clicks", "cost", "sales1d", "sales7d", "sales14d"
        ]

    body: dict[str, Any] = {
        "name": name,
        "startDate": start_date,
        "endDate": end_date,
        "configuration": {
            "adProduct": "SPONSORED_PRODUCTS",
            "groupBy": group_by,
            "columns": columns,
            "reportTypeId": v3_report_type_id,
            "timeUnit": "DAILY",
            "format": "GZIP_JSON",
        },
    }
    last_error: str | None = None
    for prefix in REPORTING_PREFIXES:
        path = f"{prefix}/reports"
        # Small internal retry for transient errors
        for attempt in range(3):
            r = client.request(
                "POST",
                path,
                json=body,
                headers={
                    "Content-Type": CONTENT_CREATE,
                    "Accept": CONTENT_REPORT,
                },
            )
            if r.status_code == 200:
                return r.json()["reportId"]
            
            # Handle 425 Duplicate Request by extracting reportId from message
            if r.status_code == 425:
                try:
                    data = r.json()
                    msg = data.get("message", "")
                    match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", msg)
                    if match:
                        rid = match.group(0)
                        logger.info(f"Duplicate request detected. Resuming with existing reportId: {rid}")
                        return rid
                except Exception:
                    pass
            
            last_error = f"{path} -> {r.status_code}: {r.text}"
            if r.status_code == 429:
                if attempt < 2:
                    time.sleep(20 * (attempt + 1))
                    continue
            
            logger.warning(
                "create_report_failed_endpoint", 
                extra={"path": path, "status": r.status_code, "body": r.text, "payload": body}
            )
            break # Non-429 or exhausted retries
        
    raise RuntimeError(f"Create report failed on all known endpoints. Last error: {last_error}")


def create_sp_campaign_daily_report(client: AdsApiClient, *, name: str, start_date: str, end_date: str) -> str:
    """Alias for backward compatibility."""
    return create_sp_daily_report(client, name=name, start_date=start_date, end_date=end_date, report_type="spCampaigns")


def get_report_status(client: AdsApiClient, report_id: str) -> dict[str, Any]:
    last_error: str | None = None
    for prefix in REPORTING_PREFIXES:
        path = f"{prefix}/reports/{report_id}"
        # Small internal retry for transient 429
        for attempt in range(3):
            r = client.request(
                "GET",
                path,
                headers={"Accept": CONTENT_REPORT},
            )
            if r.status_code < 400:
                return r.json()
            
            last_error = f"{path} -> {r.status_code}: {r.text}"
            if r.status_code == 429:
                # Check for Retry-After header (seconds)
                retry_after = r.headers.get("Retry-After")
                try:
                    wait_sec = float(retry_after) if retry_after else (30.0 * (attempt + 1))
                except ValueError:
                    wait_sec = 30.0 * (attempt + 1)
                
                # Cap the internal wait to avoid blocking the main thread too long
                wait_sec = min(wait_sec, 90.0)
                
                if attempt < 2:
                    logger.info(f"Throttled on status check. Waiting {wait_sec:.0f}s (attempt {attempt+1}/3)")
                    time.sleep(wait_sec)
                    continue
            break # Non-429 or exhausted retries

    raise RuntimeError(f"Get report failed on all known endpoints. Last error: {last_error}")


def download_report_url(url: str, timeout: float = 120.0) -> bytes:
    with httpx.Client(timeout=timeout, follow_redirects=True) as http:
        rr = http.get(url)
        rr.raise_for_status()
        return rr.content


def run_report_pipeline(
    client: AdsApiClient,
    *,
    run_id: str,
    start_date: str,
    end_date: str,
    raw_dir: str,
    progress: ProgressCallback = _noop_progress,
    resume_report_id: str | None = None,
    max_poll_minutes: float | None = None,
    max_poll_attempts: int | None = None,
    report_type: str = "spCampaigns",
    group_by: list[str] | None = None,
) -> ReportArtifacts:
    """
    Create report (unless resume_report_id), poll until COMPLETED or FAILED, download.
    Stops on wall-clock max_poll_minutes (default from report_config).
    """
    os.makedirs(raw_dir, exist_ok=True)
    max_min = float(max_poll_minutes if max_poll_minutes is not None else MAX_POLL_MINUTES)
    hard_attempts = int(max_poll_attempts if max_poll_attempts is not None else MAX_POLL_ATTEMPTS_SAFETY)
    name = f"sp-{report_type}-{run_id}"

    report_id: str | None = resume_report_id

    if report_id:
        progress("resume", f"Resuming pending report {report_id} (no new create)")
        _write_report_job(
            raw_dir,
            run_id=run_id,
            report_id=report_id,
            start_date=start_date,
            end_date=end_date,
            state="polling",
            last_status="RESUME",
        )
    else:
        progress("create", f"Submitting {report_type} report request")
        last_exc: Exception | None = None
        for attempt in range(CREATE_RETRY_ATTEMPTS):
            try:
                report_id = create_sp_daily_report(
                    client,
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    report_type=report_type,
                    group_by=group_by,
                )
                break
            except Exception as e:
                last_exc = e
                msg = str(e)
                cd = 30.0
                if "429" in msg or "Quota" in msg:
                    cd = 60.0
                progress("retry", f"Create attempt {attempt + 1} failed; cooldown {cd:.0f}s: {e}")
                logger.warning("create_report_retry", extra={"attempt": attempt, "error": str(e)})
                time.sleep(cd)
        if report_id is None:
            raise RuntimeError(f"Could not create report: {last_exc}") from last_exc

        assert report_id is not None
        meta_path = os.path.join(raw_dir, "report_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {"reportId": report_id, "startDate": start_date, "endDate": end_date, "runId": run_id, "reportType": report_type},
                f,
                indent=2,
            )
        _write_report_job(
            raw_dir,
            run_id=run_id,
            report_id=report_id,
            start_date=start_date,
            end_date=end_date,
            state="polling",
            last_status="CREATED",
        )

    assert report_id is not None
    poll_t0 = time.monotonic()
    download_url: str | None = None
    i = 0
    while i < hard_attempts:
        elapsed = time.monotonic() - poll_t0
        if elapsed > max_min * 60:
            _write_report_job(
                raw_dir,
                run_id=run_id,
                report_id=report_id,
                start_date=start_date,
                end_date=end_date,
                state="timeout",
                attempt_count=i,
                last_status="TIMEOUT",
            )
            raise ReportPollTimeout(
                report_id,
                raw_dir,
                elapsed_seconds=elapsed,
                max_minutes=max_min,
            )

        try:
            st = get_report_status(client, report_id)
        except Exception as e:
            msg = str(e)
            progress("poll_error", f"{msg}; retrying after cooldown")
            cd = _cooldown_from_response(500, msg)
            if "429" in msg:
                cd = max(cd, 60.0)
            time.sleep(cd)
            i += 1
            continue

        status = (st.get("status") or st.get("processingStatus") or "").upper()
        interval = compute_poll_interval_seconds(i)

        _write_report_job(
            raw_dir,
            run_id=run_id,
            report_id=report_id,
            start_date=start_date,
            end_date=end_date,
            state="polling",
            attempt_count=i + 1,
            last_status=status or "UNKNOWN",
        )

        if status in ("COMPLETED", "SUCCESS"):
            download_url = st.get("url") or (st.get("location") if isinstance(st.get("location"), str) else None)
            if not download_url and isinstance(st.get("completionDetails"), dict):
                download_url = st["completionDetails"].get("url")
            if not download_url:
                raise RuntimeError(f"Completed but no URL in response: {st}")
            break
        if status in ("FAILURE", "FAILED", "CANCELLED"):
            raise RuntimeError(f"Report failed: {st}")

        progress(
            "poll",
            f"status={status or 'unknown'} · attempt {i + 1} · elapsed {elapsed:.0f}s · next poll in ~{interval:.0f}s",
        )
        time.sleep(interval)
        i += 1

    if not download_url:
        raise RuntimeError("Report did not complete (hard attempt cap)")

    _write_report_job(
        raw_dir,
        run_id=run_id,
        report_id=report_id,
        start_date=start_date,
        end_date=end_date,
        state="completed",
        attempt_count=i + 1,
        last_status="COMPLETED",
    )

    progress("download", "Downloading report file")
    raw_bytes = download_report_url(download_url)
    out_file = os.path.join(raw_dir, "report_download.bin")
    with open(out_file, "wb") as f:
        f.write(raw_bytes)
    json_bytes = decompress_if_gzip(raw_bytes)
    json_name = f"sp_{report_type}_{run_id}.json"
    json_path = os.path.join(raw_dir, json_name)
    with open(json_path, "wb") as f:
        f.write(json_bytes)

    return ReportArtifacts(
        report_id=report_id,
        raw_dir=raw_dir,
        downloaded_path=out_file,
        extracted_json_path=json_path,
        payload_bytes=raw_bytes,
    )


def decompress_if_gzip(data: bytes) -> bytes:
    if len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B:
        return gzip.decompress(data)
    return data
