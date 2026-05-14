"""CLI entrypoint for non-UI runs (e.g. future cron)."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from amazon_ads_app.auth import LwaTokenProvider
from amazon_ads_app.config import load_app_config, load_profiles
from amazon_ads_app.healthcheck import auth_debug_info, validate_all_regions_unscoped
from amazon_ads_app.logging_setup import setup_logging
from amazon_ads_app.pipeline import run_profile
from amazon_ads_app.profile_cache import (
    build_cache_now,
    default_cache_path,
    load_cache,
    save_cache,
)
from amazon_ads_app.profile_discovery import discover_all_profiles, resolve_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Amazon Ads SP campaign report for one profile.")
    parser.add_argument(
        "--profile-id",
        type=int,
        default=None,
        help="Advertising profile id (from discovery cache or profiles.yaml)",
    )
    parser.add_argument(
        "--all-profiles",
        action="store_true",
        help="Fetch reports for ALL profiles in the cache/YAML",
    )
    parser.add_argument("--days", type=int, default=5, help="Number of calendar days (default 5)")
    parser.add_argument(
        "--max-poll-minutes",
        type=float,
        default=None,
        help=f"Max wall-clock minutes to wait for async report (default from app config)",
    )
    parser.add_argument(
        "--resume-report-id",
        default=None,
        help="Resume polling an existing report id (requires --resume-raw-dir)",
    )
    parser.add_argument(
        "--resume-raw-dir",
        default=None,
        help="Raw directory from a previous run (contains report_job.json)",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover profiles across all regions, print JSON to stdout, and exit",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Discover profiles and write data/cache/profiles_cache.json, then exit",
    )
    parser.add_argument(
        "--validate-auth",
        action="store_true",
        help="GET List Profiles on each regional host; exit 0 if any region succeeds",
    )
    args = parser.parse_args()

    try:
        app = load_app_config()
    except ValueError as e:
        raise SystemExit(f"Invalid configuration: {e}") from e
    setup_logging(app.project_root / "logs")
    log = logging.getLogger(__name__)

    if args.validate_auth:
        tp = LwaTokenProvider(
            app.lwa_client_id,
            app.lwa_client_secret,
            app.lwa_refresh_token,
        )
        results = validate_all_regions_unscoped(app, tp)
        any_ok = False
        for reg, (ok, msg) in sorted(results.items()):
            line = "OK" if ok else msg
            print(f"{reg}: {line}")
            any_ok = any_ok or ok
        if os.environ.get("AMAZON_ADS_DEBUG_AUTH", "").strip().lower() in ("1", "true", "yes"):
            print(json.dumps(auth_debug_info(app, tp), indent=2))
        sys.exit(0 if any_ok else 1)

    if args.discover:
        profiles, errors = discover_all_profiles(app)
        out = {
            "profiles": [
                {"id": p.id, "region": p.region, "display_name": p.display_name} for p in profiles
            ],
            "errors": errors,
        }
        print(json.dumps(out, indent=2))
        sys.exit(0)

    if args.refresh_cache:
        profiles, errors = discover_all_profiles(app)
        path = default_cache_path(app.project_root)
        save_cache(path, build_cache_now(profiles, errors))
        log.info("cache_refreshed", extra={"path": str(path), "count": len(profiles)})
        print(f"Wrote {len(profiles)} profile(s) to {path}")
        if errors:
            print("Warnings per region:", file=sys.stderr)
            for k, v in errors.items():
                print(f"  {k}: {v[:200]}", file=sys.stderr)
        sys.exit(0)

    if args.all_profiles:
        from amazon_ads_app.pipeline import run_bulk_profiles
        from amazon_ads_app.export import export_dataframe
        import pandas as pd

        cached = load_cache(default_cache_path(app.project_root))
        profiles = cached.profiles if cached else []
        if not profiles:
            profiles, _ = discover_all_profiles(app)
        
        if not profiles:
            raise SystemExit("No profiles found to fetch.")

        print(f"Starting bulk fetch for {len(profiles)} profiles...")
        results = run_bulk_profiles(app, profiles, days=args.days, progress=lambda s, d: print(f"[{s}] {d}"))
        
        if not results:
            print("No data retrieved.")
            return

        all_dfs = []
        for r in results:
            df = r.wide.copy()
            df.insert(0, "profile_id", r.profile.id)
            df.insert(1, "region", r.profile.region)
            df.insert(2, "currency", r.profile.currency_code or "")
            all_dfs.append(df)
        
        final_df = pd.concat(all_dfs, ignore_index=True)
        run_day = datetime.now(timezone.utc).date().isoformat()
        stem = f"GLOBAL_BULK_{run_day}"
        out_dir = app.project_root / "data" / "processed" / stem
        csv_p, xlsx_p = export_dataframe(final_df, out_dir, stem=stem)
        
        print(f"\nSuccessfully aggregated {len(all_dfs)} profiles.")
        print(f"CSV: {csv_p}")
        print(f"XLSX: {xlsx_p}")
        sys.exit(0)

    if args.profile_id is None:
        parser.error("Provide --profile-id or use --discover / --refresh-cache")

    log.info("cli_start", extra={"profile_id": args.profile_id})

    prof = resolve_profile(app, args.profile_id)
    if prof is None:
        # Helpful hint: list yaml ids
        hint = ""
        if app.profiles_path.exists():
            ids = [p.id for p in load_profiles(app.profiles_path)]
            hint = f" Known YAML ids: {ids}." if ids else ""
        cached = load_cache(default_cache_path(app.project_root))
        if cached and cached.profiles:
            hint += f" Cached ids: {[p.id for p in cached.profiles]}."
        raise SystemExit(f"Unknown profile id {args.profile_id}.{hint}")

    run_kwargs: dict = {"days": args.days}
    if args.max_poll_minutes is not None:
        run_kwargs["max_poll_minutes"] = args.max_poll_minutes
    if args.resume_report_id or args.resume_raw_dir:
        if not args.resume_report_id or not args.resume_raw_dir:
            parser.error("Both --resume-report-id and --resume-raw-dir are required together")
        run_kwargs["resume_report_id"] = args.resume_report_id
        run_kwargs["resume_raw_dir"] = Path(args.resume_raw_dir)

    result = run_profile(app, prof, **run_kwargs)
    print(f"Done. JSON artifact: {result.json_path}")


if __name__ == "__main__":
    main()
