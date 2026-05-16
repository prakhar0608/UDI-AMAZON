"""End-to-end run for one advertising profile."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from amazon_ads_app.api_client import AdsApiClient
from amazon_ads_app.auth import LwaTokenProvider
from amazon_ads_app.config import AppConfig, ProfileConfig
from amazon_ads_app.date_windows import safe_last_n_days, date_range_from_strings
from amazon_ads_app.export import sanitize_filename_part
from amazon_ads_app.metrics import aggregate_campaign_daily
from amazon_ads_app.parse_report import parse_report_payload_with_meta
from amazon_ads_app.pivot_wide import pivot_campaigns_wide
from amazon_ads_app.regions import base_url_for_region
from amazon_ads_app.report_config import MAX_POLL_MINUTES
from amazon_ads_app.reports_v3 import run_report_pipeline, create_sp_daily_report, decompress_if_gzip, get_report_status, download_report_url
from amazon_ads_app.asin_ranges import load_asin_ranges, apply_asin_ranges
from amazon_ads_app.report_config import compute_poll_interval_seconds
import concurrent.futures
import time

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str], None]


def _noop(s: str, d: str) -> None:
    pass


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    profile: ProfileConfig
    start_date: str
    end_date: str
    dates: list[str]
    wide: pd.DataFrame
    long_daily: pd.DataFrame
    raw_dir: Path
    json_path: Path
    csv_name: str
    xlsx_name: str
    timezone_used: str
    used_missing_date_fallback: bool
    is_aggregated: bool = False
    report_type: str = "spCampaigns"


def infer_daily_rows_from_missing_date(df: pd.DataFrame, dates: list[str]) -> tuple[pd.DataFrame, bool]:
    """
    Infer day assignment from row order when payload omits row-level date.
    Returns (daily_df, inferred_ok).
    """
    if df.empty:
        return df, True
    if not dates:
        return df, False

    work = df.reset_index(drop=False).rename(columns={"index": "_row_order"})
    out: list[pd.DataFrame] = []
    expected = len(dates)
    
    # Identify grouping columns
    potential_group = ["campaign_id", "campaign_name", "ad_group_id", "ad_group_name", "range", "subcat", "asin", "sku", "targeting", "targeting_type"]
    group_cols = [c for c in potential_group if c in df.columns]
    
    if not group_cols:
        # Fallback if no known ID columns are found
        df_assigned = df.copy()
        df_assigned["date"] = dates[:len(df)] if len(df) <= len(dates) else (dates * (len(df)//len(dates) + 1))[:len(df)]
        return df_assigned, True

    for _, grp in work.groupby(group_cols, sort=False):
        g = grp.sort_values("_row_order").copy()
        n = len(g)
        if n <= expected:
            assign_dates = dates[-n:]
            g["date"] = assign_dates
        else:
            # Keep most recent expected rows when API returns extra rows.
            g = g.iloc[-expected:].copy()
            g["date"] = dates[:]
        out.append(g[group_cols + ["date", "spend", "sales"]])
    return pd.concat(out, ignore_index=True), True


def _build_dataframes_from_payload(
    payload_bytes: bytes,
    dates: list[str],
    profile: ProfileConfig,
    _log_progress: ProgressCallback,
    report_type: str = "spCampaigns",
    project_root: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
    parsed = parse_report_payload_with_meta(payload_bytes)
    long_df = parsed.dataframe
    
    fallback = False
    _log_progress("parse", f"parsed_rows={len(long_df)} has_row_date={parsed.has_row_date}")
    
    if not long_df.empty and parsed.has_row_date:
        valid_dates = long_df["date"][(long_df["date"] != "NaT") & (long_df["date"] != "")]
        if not valid_dates.empty:
            _log_progress("parse", f"payload_date_range={valid_dates.min()}..{valid_dates.max()}")
        before = len(long_df)
        long_df = long_df[long_df["date"].isin(dates)]
        _log_progress("parse", f"rows_after_window_filter={len(long_df)} from={before}")
    elif not long_df.empty:
        fallback = True
        long_df, _ = infer_daily_rows_from_missing_date(long_df, dates)
        _log_progress("warn", "payload has no row-level date; inferring day sequence from row order")

    # Apply ASIN ranges/subcat mapping if project_root is provided
    if not long_df.empty and project_root and "asin" in long_df.columns:
        mapping = load_asin_ranges(project_root, profile.id)
        if mapping:
            long_df = apply_asin_ranges(long_df, mapping)
            _log_progress("enrich", f"Applied ASIN mapping for profile {profile.id}")

    # Apply the product-wise filter AFTER date inference and enrichment
    if report_type == "spProducts" and not long_df.empty:
        # Keep everything we might need for the dashboard, including enriched fields
        keep_cols = ["asin", "range", "subcat", "date", "spend", "sales", "campaign_id", "campaign_name", "ad_group_id", "ad_group_name"]
        long_df = long_df[[c for c in keep_cols if c in long_df.columns]].copy()
        _log_progress("clean", f"Product-wise filter applied: kept {list(long_df.columns)}")

    long_df = aggregate_campaign_daily(long_df, report_type=report_type)
    wide = pivot_campaigns_wide(long_df, dates, report_type=report_type)
    return wide, long_df, fallback


def build_result_from_json_artifact(
    app: AppConfig,
    profile: ProfileConfig,
    json_path: Path,
    *,
    days: int = 5,
    run_id: str = "cached_json",
) -> PipelineResult:
    """Build PipelineResult directly from an extracted JSON artifact."""
    start_date, end_date, dates, tz_used = safe_last_n_days(days, profile.timezone)
    payload_bytes = json_path.read_bytes()

    def _log(_s: str, _d: str) -> None:
        return

    # Try to infer report_type from filename
    report_type = "spCampaigns"
    if "spAdGroups" in json_path.name:
        report_type = "spAdGroups"
    elif "spTargeting" in json_path.name:
        report_type = "spTargeting"
    elif "spProducts" in json_path.name:
        report_type = "spProducts"

    wide, long_df, fallback = _build_dataframes_from_payload(
        payload_bytes, 
        dates, 
        profile, 
        _log, 
        report_type=report_type,
        project_root=app.project_root
    )
    slug = sanitize_filename_part(profile.display_name)
    run_day = datetime.now(timezone.utc).date().isoformat()
    
    stem = f"{slug}_{run_day}_{report_type}"
    return PipelineResult(
        run_id=run_id,
        profile=profile,
        start_date=start_date,
        end_date=end_date,
        dates=dates,
        wide=wide,
        long_daily=long_df,
        raw_dir=json_path.parent,
        json_path=json_path,
        csv_name=f"{stem}.csv",
        xlsx_name=f"{stem}.xlsx",
        timezone_used=tz_used,
        used_missing_date_fallback=fallback,
        report_type=report_type,
    )


def run_bulk_profiles(
    app: AppConfig,
    profiles: list[ProfileConfig],
    *,
    progress: ProgressCallback = _noop,
    days: int = 5,
    max_poll_minutes: float | None = None,
    report_type: str = "spCampaigns",
    explicit_start_date: str | None = None,
    explicit_end_date: str | None = None,
) -> list[PipelineResult]:
    """
    Fetch and aggregate data for multiple profiles by creating all reports upfront,
    then polling concurrently.
    """
    if not profiles:
        return []

    results: list[PipelineResult] = []
    token_provider = LwaTokenProvider(
        app.lwa_client_id,
        app.lwa_client_secret,
        app.lwa_refresh_token,
    )

    pending_jobs = []
    run_day = datetime.now(timezone.utc).date().isoformat()

    # Step 1: Create reports
    for p in profiles:
        try:
            if explicit_start_date and explicit_end_date:
                start_date, end_date, dates = date_range_from_strings(explicit_start_date, explicit_end_date)
                tz_used = p.timezone or "UTC"
            else:
                start_date, end_date, dates, tz_used = safe_last_n_days(days, p.timezone)
            run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
            base = base_url_for_region(p.region)
            
            progress("create", f"Submitting {report_type} report for {p.display_name} ({p.region})")
            with AdsApiClient(base, app.lwa_client_id, token_provider, profile_id=p.id) as client:
                report_id = create_sp_daily_report(
                    client, 
                    name=f"bulk-{report_type}-{run_id}", 
                    start_date=start_date, 
                    end_date=end_date,
                    report_type=report_type,
                )
            
            pending_jobs.append({
                "profile": p,
                "report_id": report_id,
                "base_url": base,
                "dates": dates,
                "run_id": run_id,
                "start_date": start_date,
                "end_date": end_date,
                "tz_used": tz_used,
                "raw_dir": app.project_root / "data" / "raw" / p.region / sanitize_filename_part(p.display_name) / run_id
            })
        except Exception as e:
            progress("error", f"Failed to start {report_type} report for {p.display_name} ({p.region}): {e}")

    # Step 2: Poll concurrently using ThreadPoolExecutor
    if pending_jobs:
        poll_t0 = time.monotonic()
        mp = float(max_poll_minutes if max_poll_minutes is not None else MAX_POLL_MINUTES)
        attempt = 0
        retry_after_map: dict[str, float] = {}
        
        def process_job(job):
            p = job["profile"]
            rid = job["report_id"]
            
            if rid in retry_after_map and time.monotonic() < retry_after_map[rid]:
                return "pending", job

            try:
                with AdsApiClient(job["base_url"], app.lwa_client_id, token_provider, profile_id=p.id) as client:
                    st_res = get_report_status(client, rid)
                
                status = (st_res.get("status") or st_res.get("processingStatus") or "").upper()
                if status in ("COMPLETED", "SUCCESS"):
                    url = st_res.get("url") or (st_res.get("location") if isinstance(st_res.get("location"), str) else None)
                    if not url and isinstance(st_res.get("completionDetails"), dict):
                        url = st_res["completionDetails"].get("url")
                    
                    if url:
                        raw_bytes = download_report_url(url)
                        job["raw_dir"].mkdir(parents=True, exist_ok=True)
                        json_path = job["raw_dir"] / f"sp_{report_type}_{job['run_id']}.json"
                        json_path.write_bytes(decompress_if_gzip(raw_bytes))
                        
                        wide, long_df, fallback = _build_dataframes_from_payload(
                            raw_bytes, 
                            job["dates"], 
                            p, 
                            lambda s, d: None, 
                            report_type=report_type,
                            project_root=app.project_root
                        )
                        slug = sanitize_filename_part(p.display_name)
                        stem = f"{slug}_{run_day}_{report_type}"
                        
                        return "success", PipelineResult(
                            run_id=job["run_id"],
                            profile=p,
                            start_date=job["start_date"],
                            end_date=job["end_date"],
                            dates=job["dates"],
                            wide=wide,
                            long_daily=long_df,
                            raw_dir=job["raw_dir"],
                            json_path=json_path,
                            csv_name=f"{stem}.csv",
                            xlsx_name=f"{stem}.xlsx",
                            timezone_used=job["tz_used"],
                            used_missing_date_fallback=fallback,
                            report_type=report_type,
                        )
                elif status in ("FAILURE", "FAILED", "CANCELLED"):
                    return "error", f"Report failed for {p.display_name}: {st_res}"
                else:
                    return "pending", job
            except Exception as e:
                msg = str(e)
                if "429" in msg or "Throttled" in msg:
                    retry_after_map[rid] = time.monotonic() + 30.0
                    return "pending", job
                return "error", f"Error for {p.display_name}: {e}"

        while pending_jobs and (time.monotonic() - poll_t0 < mp * 60):
            progress("poll", f"Polling {len(pending_jobs)} pending {report_type} reports (Attempt {attempt+1})...")
            still_pending = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_job = {executor.submit(process_job, job): job for job in pending_jobs}
                for future in concurrent.futures.as_completed(future_to_job):
                    res_type, data = future.result()
                    if res_type == "success":
                        results.append(data)
                        progress("download", f"Synthesis complete for {data.profile.display_name}")
                    elif res_type == "error":
                        progress("error", data)
                    else:
                        still_pending.append(data)
            
            pending_jobs = still_pending
            if pending_jobs:
                interval = compute_poll_interval_seconds(attempt)
                time.sleep(interval)
                attempt += 1
        
        if pending_jobs:
            progress("timeout", f"{len(pending_jobs)} regions timed out after {mp} minutes.")

    return results


def _find_today_json_artifact_path(project_root: Path, profile: ProfileConfig, report_type: str = "spCampaigns") -> Path:
    slug = sanitize_filename_part(profile.display_name)
    region_dir = project_root / "data" / "raw" / profile.region / slug
    if not region_dir.exists():
        raise FileNotFoundError()
    today_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    candidates = sorted(region_dir.glob(f"{today_prefix}T*/sp_{report_type}_*.json"))
    if not candidates:
        # Fallback to older naming if it was sp_campaigns
        if report_type == "spCampaigns":
             candidates = sorted(region_dir.glob(f"{today_prefix}T*/sp_campaigns_*.json"))
        
    if not candidates:
        raise FileNotFoundError()
    return candidates[-1]


def run_profile(
    app: AppConfig,
    profile: ProfileConfig,
    *,
    progress: ProgressCallback = _noop,
    days: int = 5,
    mtd: bool = False,
    resume_report_id: str | None = None,
    resume_raw_dir: Path | None = None,
    max_poll_minutes: float | None = None,
    report_type: str = "spCampaigns",
    start_date: str | None = None,
    end_date: str | None = None,
) -> PipelineResult:
    if profile.id <= 0:
        raise ValueError("Invalid advertising profile id.")
    if not str(profile.region).strip():
        raise ValueError("Profile region is required.")
    if not str(profile.display_name).strip():
        raise ValueError("Profile display_name is required.")

    if start_date and end_date:
        # Use provided dates
        sd_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        ed_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        dates: list[str] = []
        cur = sd_obj
        while cur <= ed_obj:
            dates.append(cur.isoformat())
            cur += timedelta(days=1)
        tz_used = profile.timezone or "UTC"
    elif mtd:
        from amazon_ads_app.date_windows import mtd_till_yesterday
        start_date, end_date, dates = mtd_till_yesterday(profile.timezone or "UTC")
        tz_used = profile.timezone or "UTC"
    else:
        start_date, end_date, dates, tz_used = safe_last_n_days(days, profile.timezone)
    
    slug = sanitize_filename_part(profile.display_name)

    if resume_report_id:
        if resume_raw_dir is None:
            raise ValueError("resume_raw_dir is required when resume_report_id is set.")
        raw_dir = Path(resume_raw_dir).resolve()
        if not raw_dir.is_dir():
            raise ValueError(f"resume_raw_dir must exist: {raw_dir}")
        job_fp = raw_dir / "report_job.json"
        if job_fp.exists():
            jd = json.loads(job_fp.read_text(encoding="utf-8"))
            run_id = str(jd.get("runId") or jd.get("run_id") or "resume")
        else:
            run_id = "resume"
    else:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
        raw_dir = app.project_root / "data" / "raw" / profile.region / slug / run_id

    progress("init", f"Window {start_date} .. {end_date} (calendar={tz_used})")

    base = base_url_for_region(profile.region)
    token_provider = LwaTokenProvider(
        app.lwa_client_id,
        app.lwa_client_secret,
        app.lwa_refresh_token,
    )

    run_day = datetime.now(timezone.utc).date().isoformat()

    extra = {
        "run_id": run_id,
        "profile_id": profile.id,
        "region": profile.region,
        "timezone_used": tz_used,
        "currency_code": profile.currency_code or "",
        "report_type": report_type,
    }

    def _log_progress(step: str, detail: str) -> None:
        progress(step, detail)
        logger.info(
            detail,
            extra={**extra, "step": step},
        )

    _log_progress(
        "start",
        f"Single-account {report_type} report run — profile_id={profile.id} region={profile.region} run_id={run_id} "
        f"resume={bool(resume_report_id)}",
    )

    mp = float(max_poll_minutes) if max_poll_minutes is not None else float(MAX_POLL_MINUTES)
    _log_progress(
        "config",
        f"max_poll_minutes={mp} timezone={tz_used} currency={profile.currency_code or 'unknown'} days={len(dates)}",
    )

    with AdsApiClient(
        base,
        app.lwa_client_id,
        token_provider,
        profile_id=profile.id,
    ) as client:
        artifacts = run_report_pipeline(
            client,
            run_id=run_id,
            start_date=start_date,
            end_date=end_date,
            raw_dir=str(raw_dir),
            progress=_log_progress,
            resume_report_id=resume_report_id,
            max_poll_minutes=mp,
            report_type=report_type,
        )

    extracted_json_path = getattr(artifacts, "extracted_json_path", "")
    if extracted_json_path and Path(extracted_json_path).exists():
        payload_bytes = Path(extracted_json_path).read_bytes()
        json_path = Path(extracted_json_path)
    else:
        payload_bytes = artifacts.payload_bytes
        json_path = Path(artifacts.raw_dir) / f"sp_{report_type}_{run_id}.json"
    wide, long_df, fallback = _build_dataframes_from_payload(
        payload_bytes, 
        dates, 
        profile, 
        _log_progress, 
        report_type=report_type,
        project_root=app.project_root
    )
    stem = f"{slug}_{run_day}_{report_type}"
    _log_progress("done", f"Prepared dataframe from {json_path}")

    return PipelineResult(
        run_id=run_id,
        profile=profile,
        start_date=start_date,
        end_date=end_date,
        dates=dates,
        wide=wide,
        long_daily=long_df,
        raw_dir=Path(artifacts.raw_dir),
        json_path=json_path,
        csv_name=f"{stem}.csv",
        xlsx_name=f"{stem}.xlsx",
        timezone_used=tz_used,
        used_missing_date_fallback=fallback,
        report_type=report_type,
    )
