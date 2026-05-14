"""Streamlit UI for Amazon Ads SP campaign reporting."""

from __future__ import annotations

import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode

from amazon_ads_app.auth import LwaTokenProvider
from amazon_ads_app.config import ProfileConfig, load_app_config, load_profiles
from amazon_ads_app.date_windows import (
    safe_last_n_days, 
    last_n_days_till_yesterday, 
    mtd_till_yesterday
)
from amazon_ads_app.export import dataframe_to_csv_xlsx_bytes, sanitize_filename_part
from amazon_ads_app.healthcheck import auth_debug_info, validate_all_regions_unscoped, validate_scoped_profile
from amazon_ads_app.logging_setup import setup_logging
from amazon_ads_app.pipeline import (
    PipelineResult, 
    build_result_from_json_artifact, 
    run_profile, 
    run_bulk_profiles
)
from amazon_ads_app.reports_v3 import (
    ReportPollTimeout,
    create_sp_daily_report,
    get_report_status,
    download_report_url,
    decompress_if_gzip,
)
from amazon_ads_app.api_client import AdsApiClient
from amazon_ads_app.profile_cache import (
    build_cache_now,
    cache_is_stale,
    default_cache_path,
    load_cache,
    save_cache,
)
from amazon_ads_app.profile_discovery import discover_all_profiles
from amazon_ads_app.profile_groups import (
    filter_profiles_by_search,
    format_group_select_label,
    group_profiles_by_account,
)
from amazon_ads_app.regions import base_url_for_region
from amazon_ads_app.report_config import MAX_POLL_MINUTES, compute_poll_interval_seconds

_LOG_ROOT = Path(__file__).resolve().parent / "logs"

# Optional: warn if cache older than this many seconds (24h).
CACHE_STALE_SECONDS = 86400


@st.cache_data(show_spinner=False)
def _load_profiles_yaml_cached(path_str: str):
    return load_profiles(Path(path_str))


def _find_today_json_artifact(project_root: Path, profile: ProfileConfig, report_type: str = "spCampaigns") -> Path | None:
    slug = sanitize_filename_part(profile.display_name)
    region_dir = project_root / "data" / "raw" / profile.region / slug
    if not region_dir.exists():
        return None
    today_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    # Try new naming
    candidates = sorted(region_dir.glob(f"{today_prefix}T*/sp_{report_type}_*.json"))
    if not candidates and report_type == "spCampaigns":
        # Fallback to old naming
        candidates = sorted(region_dir.glob(f"{today_prefix}T*/sp_campaigns_*.json"))
        
    return candidates[-1] if candidates else None


def _sidebar_profiles(
    app_cfg,
) -> tuple[list[ProfileConfig] | None, str | None]:
    """
    Returns (profiles list or None if user must fix setup, error message for blocking errors).
    """
    cache_path = default_cache_path(app_cfg.project_root)

    cached = load_cache(cache_path)
    if cached and cached.errors:
        with st.sidebar.expander("Last refresh warnings (per region)", expanded=False):
            for reg, msg in sorted(cached.errors.items()):
                st.text(f"{reg}: {msg[:200]}")

    if st.sidebar.button("Refresh Accounts", type="secondary"):
        try:
            with st.spinner("Discovering profiles in all regions…"):
                profiles, errors = discover_all_profiles(app_cfg)
                save_cache(cache_path, build_cache_now(profiles, errors))
            st.session_state["discovery_flash"] = f"Loaded {len(profiles)} account(s)."
            st.rerun()
        except Exception as e:
            st.session_state["discovery_error"] = str(e)
            st.error(str(e))

    flash = st.session_state.pop("discovery_flash", None)
    if flash:
        st.sidebar.success(flash)

    disc_err = st.session_state.get("discovery_error")
    if disc_err:
        st.sidebar.warning(disc_err)

    if cached:
        st.sidebar.markdown(f"**Last fetched:** `{cached.fetched_at}`")
        if cache_is_stale(cached.fetched_at, CACHE_STALE_SECONDS):
            st.sidebar.warning("Cache may be stale; consider **Refresh accounts**.")
        if cached.profiles:
            return cached.profiles, None
        st.sidebar.info("Cache is empty. Click **Refresh accounts**.")
        return [], None

    st.sidebar.info("No account cache yet. Click **Refresh accounts**.")
    return [], None


def main() -> None:
    st.set_page_config(page_title="Amazon Ads SP Reporter", layout="wide")
    setup_logging(_LOG_ROOT)

    st.title("Amazon Ads — Sponsored Products campaigns")
    st.caption("Reporting for Campaign and Targeting levels.")

    try:
        app_cfg = load_app_config()
    except KeyError as e:
        st.error(f"Missing environment variable: {e}. Copy `.env.example` to `.env` and fill LWA credentials.")
        return
    except ValueError as e:
        st.error(f"Invalid environment configuration: {e}")
        return

    profiles, blocking = _sidebar_profiles(app_cfg)
    if blocking:
        st.error(blocking)
        return
    if profiles is None:
        return
    if not profiles:
        st.warning("No accounts available. Click **Refresh accounts** in the sidebar.")
        return

    # Sidebar: Global Actions
    if st.sidebar.button("Fetch ALL Accounts (Global Bulk)", help=f"Fetch and aggregate every account in the cache ({len(profiles)} profiles).", type="secondary"):
        st.session_state.pop("last_result", None)
        st.session_state.pop("last_error", None)
        with st.status("Performing Global Bulk Fetch (Campaign Level)...", expanded=True) as status:
            results = run_bulk_profiles(app_cfg, profiles, days=5, progress=lambda s, d: status.write(f"**{s}**: {d}"))
        if results:
            all_dfs = []
            for r in results:
                df = r.wide.copy()
                df.insert(0, "profile_id", r.profile.id)
                df.insert(1, "region", r.profile.region)
                df.insert(2, "currency", r.profile.currency_code or "")
                all_dfs.append(df)
            final_df = pd.concat(all_dfs, ignore_index=True)
            run_day = datetime.now(timezone.utc).date().isoformat()
            st.session_state["last_result"] = PipelineResult(
                run_id=f"global_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                profile=profiles[0], start_date="", end_date="", dates=[],
                wide=final_df, long_daily=pd.DataFrame(), raw_dir=app_cfg.project_root,
                json_path=Path("global_aggregated"),
                csv_name=f"GLOBAL_ALL_ACCOUNTS_{run_day}.csv",
                xlsx_name=f"GLOBAL_ALL_ACCOUNTS_{run_day}.xlsx",
                timezone_used="Multi", used_missing_date_fallback=False, is_aggregated=True
            )
            st.success(f"Successfully aggregated {len(results)} accounts.")
        else:
            st.error("Global fetch failed.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Advertising profile")
    search_q = st.sidebar.text_input("Search", value="", placeholder="Name, region, profile id…")
    filtered = filter_profiles_by_search(profiles, search_q)
    if not filtered:
        st.sidebar.warning("No profiles match your search.")
        return

    grouped = group_profiles_by_account(filtered)
    group_keys = sorted(grouped.keys(), key=lambda k: format_group_select_label(k, grouped[k]).lower())
    selected_key = st.sidebar.selectbox("Account", group_keys, format_func=lambda k: format_group_select_label(k, grouped[k]))
    members = grouped[selected_key]
    
    if len(members) == 1:
        profile = members[0]
        st.sidebar.markdown(f"**Account:** {profile.display_name}  \n**Region:** `{profile.region}`")
    else:
        sub_options = {f"{m.display_name} — {m.region}": m for m in sorted(members, key=lambda x: (x.region, x.id))}
        sub_choice = st.sidebar.selectbox("Region / profile", list(sub_options.keys()))
        profile = sub_options[sub_choice]
        st.sidebar.markdown(f"**Selected Region:** `{profile.region}`")

    # Main Tabs
    tab_campaign, tab_ad_group, tab_product = st.tabs(["Campaign Level", "Ad Group Level", "Product/ASIN Level"])

    with tab_campaign:
        st.subheader("Campaign reporting (Last 5 days till yesterday)")
        if st.button("Fetch Campaigns", type="primary"):
            st.session_state.pop("last_result", None)
            try:
                with st.status("Fetching Campaign report…") as status:
                    result = run_profile(app_cfg, profile, progress=lambda s, d: status.write(f"**{s}** — {d}"))
                st.session_state["last_result"] = result
            except Exception as e:
                st.error(str(e))

        res_c = st.session_state.get("last_result")
        if res_c and res_c.report_type not in ("spAdGroups", "spTargeting", "spProducts"):
            _display_result(res_c)

    with tab_ad_group:
        st.subheader("Ad Group Data (Till Yesterday)")
        t_range = st.radio("Date Range", ["Last 7 Days (till yesterday)", "MTD (till yesterday)"], horizontal=True, key="range_ad_group")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Fetch Single Region Ad Groups"):
                _fetch_ad_groups(app_cfg, [profile], t_range, is_bulk=False)
        with col2:
            if st.button("Fetch All Regions Ad Groups (Bulk)"):
                _fetch_ad_groups(app_cfg, members, t_range, is_bulk=True)

        res_t = st.session_state.get("last_ad_group_result")
        if res_t:
            _display_result(res_t)

    with tab_product:
        st.subheader("Product/ASIN Data (Till Yesterday)")
        p_range = st.radio("Date Range", ["Last 7 Days (till yesterday)", "MTD (till yesterday)"], horizontal=True, key="range_product")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Fetch Single Region Products"):
                _fetch_products(app_cfg, [profile], p_range, is_bulk=False)
        with col2:
            if st.button("Fetch All Regions Products (Bulk)"):
                _fetch_products(app_cfg, members, p_range, is_bulk=True)

        res_p = st.session_state.get("last_product_result")
        if res_p:
            _display_result(res_p)


def _fetch_products(app_cfg, profiles, range_label, is_bulk):
    st.session_state.pop("last_product_result", None)
    
    tz = profiles[0].timezone or "Asia/Kolkata"
    if range_label.startswith("Last 7"):
        start, end, dates = last_n_days_till_yesterday(7, tz)
    else:
        start, end, dates = mtd_till_yesterday(tz)
    
    with st.status(f"Fetching Product/ASIN Data ({range_label})...", expanded=True) as status:
        results = run_bulk_profiles(app_cfg, profiles, days=len(dates), report_type="spProducts", 
                                   progress=lambda s, d: status.write(f"**{s}**: {d}"))
    
    if results:
        all_dfs = []
        for r in results:
            df = r.wide.copy()
            df.insert(0, "profile_id", r.profile.id)
            df.insert(1, "region", r.profile.region)
            df.insert(2, "currency", r.profile.currency_code or "")
            all_dfs.append(df)
        
        final_df = pd.concat(all_dfs, ignore_index=True)
        run_day = datetime.now(timezone.utc).date().isoformat()
        slug = sanitize_filename_part(profiles[0].display_name)
        
        st.session_state["last_product_result"] = PipelineResult(
            run_id=f"product_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            profile=profiles[0],
            start_date=start,
            end_date=end,
            dates=dates,
            wide=final_df,
            long_daily=pd.DataFrame(),
            raw_dir=app_cfg.project_root,
            json_path=Path("product_aggregated"),
            csv_name=f"{slug}_PRODUCTS_{start}_to_{end}.csv",
            xlsx_name=f"{slug}_PRODUCTS_{start}_to_{end}.xlsx",
            timezone_used=tz,
            used_missing_date_fallback=False,
            is_aggregated=is_bulk,
            report_type="spProducts"
        )
        st.success(f"Successfully fetched product data for {len(results)} profile(s).")
    else:
        st.error("Product fetch failed.")


def _fetch_ad_groups(app_cfg, profiles, range_label, is_bulk):
    st.session_state.pop("last_ad_group_result", None)
    
    # Calculate dates once for the first profile's timezone (assuming they are same or close enough for bulk)
    tz = profiles[0].timezone or "Asia/Kolkata"
    if range_label.startswith("Last 7"):
        start, end, dates = last_n_days_till_yesterday(7, tz)
    else:
        start, end, dates = mtd_till_yesterday(tz)
    
    with st.status(f"Fetching Ad Group Data ({range_label})...", expanded=True) as status:
        results = run_bulk_profiles(app_cfg, profiles, days=len(dates), report_type="spAdGroups", 
                                   progress=lambda s, d: status.write(f"**{s}**: {d}"))
    
    if results:
        all_dfs = []
        for r in results:
            df = r.wide.copy()
            df.insert(0, "profile_id", r.profile.id)
            df.insert(1, "region", r.profile.region)
            df.insert(2, "currency", r.profile.currency_code or "")
            all_dfs.append(df)
        
        final_df = pd.concat(all_dfs, ignore_index=True)
        run_day = datetime.now(timezone.utc).date().isoformat()
        slug = sanitize_filename_part(profiles[0].display_name)
        
        st.session_state["last_ad_group_result"] = PipelineResult(
            run_id=f"ad_group_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            profile=profiles[0],
            start_date=start,
            end_date=end,
            dates=dates,
            wide=final_df,
            long_daily=pd.DataFrame(),
            raw_dir=app_cfg.project_root,
            json_path=Path("ad_group_aggregated"),
            csv_name=f"{slug}_AD_GROUPS_{start}_to_{end}.csv",
            xlsx_name=f"{slug}_AD_GROUPS_{start}_to_{end}.xlsx",
            timezone_used=tz,
            used_missing_date_fallback=False,
            is_aggregated=is_bulk,
            report_type="spAdGroups"
        )
        st.success(f"Successfully fetched ad group data for {len(results)} profile(s).")
    else:
        st.error("Ad group fetch failed.")


def _display_result(res: PipelineResult):
    if res.is_aggregated:
        st.info(f"**Aggregated Data for:** {res.profile.display_name} ({res.report_type})")
    else:
        st.info(f"**Account:** {res.profile.display_name} — **Region:** `{res.profile.region}` — **Window:** {res.start_date} → {res.end_date}")
    
    df = res.wide
    if df.empty:
        st.warning("No rows returned for this window.")
    else:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb.configure_default_column(filter=True, sortable=True, resizable=True)
        
        # Add % to ACoS columns in UI
        for col in df.columns:
            if "acos" in col.lower():
                gb.configure_column(col, valueFormatter="x + '%'")
        
        AgGrid(df, gridOptions=gb.build(), height=450, theme="streamlit", update_mode=GridUpdateMode.NO_UPDATE)

        csv_bytes, xlsx_bytes = dataframe_to_csv_xlsx_bytes(df)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download CSV", data=csv_bytes, file_name=res.csv_name, mime="text/csv")
        with c2:
            st.download_button("Download XLSX", data=xlsx_bytes, file_name=res.xlsx_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


if __name__ == "__main__":
    main()
