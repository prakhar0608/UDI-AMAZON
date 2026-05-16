from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import os
import sys
from datetime import datetime, timezone
import pandas as pd
from collections import defaultdict

# Add src to path so we can import amazon_ads_app
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root / "src"))

from amazon_ads_app.config import load_app_config, load_profiles
from amazon_ads_app.profile_cache import load_cache, save_cache, default_cache_path
from amazon_ads_app.pipeline import run_profile, run_bulk_profiles
from amazon_ads_app.profile_discovery import discover_all_profiles
from amazon_ads_app.export import export_dataframe, sanitize_filename_part

# Custom debug logging
debug_log_path = project_root / "debug.log"
def debug_log(msg):
    try:
        with open(debug_log_path, "a") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} - {msg}\n")
    except: pass

debug_log("Server (re)started")

app = FastAPI(title="Amazon Ads Pipeline API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Amazon Ads Pipeline API is running"}

@app.get("/api/profiles")
async def get_profiles():
    try:
        app_cfg = load_app_config()
        
        # 1. Load from YAML (Manual)
        manual_profiles = []
        if app_cfg.profiles_path.exists():
            manual_profiles = load_profiles(app_cfg.profiles_path)
            
        # 2. Load from Cache (Discovered)
        cache_path = default_cache_path(app_cfg.project_root)
        cached = load_cache(cache_path)
        discovered_profiles = cached.profiles if cached else []
        
        # Merge and dedupe by ID (YAML wins)
        merged = {p.id: p for p in discovered_profiles}
        for p in manual_profiles:
            merged[p.id] = p
            
        return [p.__dict__ for p in merged.values()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discover")
async def discover():
    try:
        app_cfg = load_app_config()
        from amazon_ads_app.auth import LwaTokenProvider
        token_provider = LwaTokenProvider(
            app_cfg.lwa_client_id,
            app_cfg.lwa_client_secret,
            app_cfg.lwa_refresh_token,
        )
        
        # Discover profiles across all regions
        profiles, errors = discover_all_profiles(app_cfg, token_provider)
        
        # Save to cache
        cache_path = default_cache_path(app_cfg.project_root)
        from amazon_ads_app.profile_cache import build_cache_now
        new_cache = build_cache_now(profiles, errors)
        save_cache(cache_path, new_cache)
        
        return [p.__dict__ for p in profiles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports")
async def get_reports():
    try:
        app_cfg = load_app_config()
        processed_dir = app_cfg.project_root / "data" / "processed"
        if not processed_dir.exists():
            return []
        
        report_groups = defaultdict(dict)
        for f in processed_dir.glob("**/*.*"):
            if f.suffix.lower() not in ('.csv', '.xlsx'):
                continue
            
            stem = f.stem
            report_groups[stem]['name'] = stem
            rel_path = str(f.relative_to(processed_dir)).replace('\\', '/')
            
            if 'created_at' not in report_groups[stem] or f.stat().st_mtime > os.path.getmtime(processed_dir / report_groups[stem].get('full_path_ref', rel_path)):
                report_groups[stem]['created_at'] = datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                report_groups[stem]['full_path_ref'] = rel_path

            if f.suffix.lower() == '.csv':
                report_groups[stem]['csv'] = rel_path
            elif f.suffix.lower() == '.xlsx':
                report_groups[stem]['xlsx'] = rel_path
        
        reports_list = list(report_groups.values())
        return sorted(reports_list, key=lambda x: x["created_at"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/download/{filename:path}")
async def download_report(filename: str):
    try:
        app_cfg = load_app_config()
        processed_dir = app_cfg.project_root / "data" / "processed"
        file_path = processed_dir / filename
        
        if not str(file_path.resolve()).startswith(str(processed_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/preview/{filename:path}")
async def preview_report(filename: str):
    """Returns the first 100 rows of a report as JSON for dashboard viewing."""
    try:
        app_cfg = load_app_config()
        processed_dir = app_cfg.project_root / "data" / "processed"
        file_path = processed_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        df = pd.read_csv(file_path)
        # Handle cases with too few rows gracefully
        preview_data = df.head(100).fillna('').to_dict(orient="records")
        return {
            "columns": df.columns.tolist(),
            "data": preview_data,
            "total_rows": len(df)
        }
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=f"Failed to parse report: {e}")

@app.get("/api/analytics/client/{profile_id}")
async def get_client_analytics(profile_id: int):
    try:
        app_cfg = load_app_config()
        processed_dir = app_cfg.project_root / "data" / "processed"
        
        cache_path = default_cache_path(app_cfg.project_root)
        cached = load_cache(cache_path)
        profile = next((p for p in cached.profiles if p.id == profile_id), None)
        if not profile:
            return {"spend": 0, "sales": 0, "roas": 0, "currency": "USD", "last_sync": None}
        
        slug = sanitize_filename_part(profile.display_name)
        currency = profile.currency_code or "USD"
        
        daily_metrics = defaultdict(lambda: {"spend": 0.0, "sales": 0.0})
        client_files = list(processed_dir.glob(f"**/{slug}*_spCampaigns.csv"))
        
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        last_sync = None
        
        for f in client_files:
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                if not last_sync or mtime > last_sync:
                    last_sync = mtime
                
                df = pd.read_csv(f)
                spend_cols = [c for c in df.columns if c.startswith('spend_')]
                for col in spend_cols:
                    date_part = col.replace('spend_', '')
                    if date_part.startswith(current_month):
                        daily_metrics[date_part]["spend"] = max(daily_metrics[date_part]["spend"], df[col].sum())
                
                sales_cols = [c for c in df.columns if c.startswith('sales_')]
                for col in sales_cols:
                    date_part = col.replace('sales_', '')
                    if date_part.startswith(current_month):
                        daily_metrics[date_part]["sales"] = max(daily_metrics[date_part]["sales"], df[col].sum())
            except:
                continue
        
        total_spend = sum(m["spend"] for m in daily_metrics.values())
        total_sales = sum(m["sales"] for m in daily_metrics.values())
        roas = total_sales / total_spend if total_spend > 0 else 0
        
        return {
            "spend": round(total_spend, 2),
            "sales": round(total_sales, 2),
            "roas": round(roas, 2),
            "currency": currency,
            "last_sync": last_sync
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fetch/{profile_id}")
async def fetch_report(
    profile_id: int, 
    report_type: str = "spCampaigns", 
    days: int = 5, 
    mtd: bool = False,
    start_date: str | None = None,
    end_date: str | None = None
):
    try:
        app_cfg = load_app_config()
        cache_path = default_cache_path(app_cfg.project_root)
        cached = load_cache(cache_path)
        profiles_list = cached.profiles if cached else []
        
        # Also check manual profiles if not in cache
        if not any(p.id == profile_id for p in profiles_list):
            if app_cfg.profiles_path.exists():
                profiles_list.extend(load_profiles(app_cfg.profiles_path))
        
        profile = next((p for p in profiles_list if p.id == profile_id), None)
        if not profile: raise HTTPException(status_code=404, detail="Profile not found")
        
        # Priority: Explicit range > MTD > Days
        result = run_profile(
            app_cfg, 
            profile, 
            report_type=report_type, 
            days=days,
            mtd=mtd,
            start_date=start_date,
            end_date=end_date
        )
        
        processed_dir = app_cfg.project_root / "data" / "processed"
        slug = sanitize_filename_part(profile.display_name)
        run_day = datetime.now(timezone.utc).date().isoformat()
        stem = f"{slug}_{run_day}_{report_type}"
        out_dir = processed_dir / stem
        export_dataframe(result.wide, out_dir, stem=stem, long_df=result.long_daily)
        
        return {
            "status": "success", "run_id": result.run_id, 
            "csv_name": f"{stem}/{stem}.csv", "xlsx_name": f"{stem}/{stem}.xlsx",
            "report_type": report_type,
            "start_date": result.start_date,
            "end_date": result.end_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import threading
import uuid as _uuid

# In-memory job store
_jobs: dict[str, dict] = {}

class BulkFetchRequest(BaseModel):
    ids: list[int]
    report_type: str = "spCampaigns"
    start_date: str | None = None
    end_date: str | None = None

def _run_export_job(job_id: str, ids: list[int], report_type: str, start_date: str | None, end_date: str | None):
    """Background worker that runs the Amazon report pipeline."""
    try:
        _jobs[job_id]["status"] = "running"
        _jobs[job_id]["message"] = "Initializing..."
        
        app_cfg = load_app_config()
        cache_path = default_cache_path(app_cfg.project_root)
        cached = load_cache(cache_path)
        
        all_profiles = cached.profiles if cached else []
        if app_cfg.profiles_path.exists():
            all_profiles.extend(load_profiles(app_cfg.profiles_path))
            
        target_profiles = [p for p in all_profiles if p.id in ids]
        debug_log(f"[JOB {job_id}] Found {len(target_profiles)} target profiles for ids {ids}")
        
        if not target_profiles:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["message"] = "No valid profiles found for given IDs."
            return

        _jobs[job_id]["message"] = f"Submitting {report_type} report..."
        
        def _inner_log(s, m):
            debug_log(f"[JOB {job_id}][{s.upper()}] {m}")
            _jobs[job_id]["message"] = f"[{s.upper()}] {m}"

        results = run_bulk_profiles(
            app_cfg,
            target_profiles,
            progress=_inner_log,
            days=7,
            report_type=report_type,
            explicit_start_date=start_date,
            explicit_end_date=end_date,
        )
        debug_log(f"[JOB {job_id}] run_bulk_profiles returned {len(results)} results")
        
        if not results:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["message"] = "No data returned. The report may have failed on Amazon's side."
            return
        
        processed_dir = app_cfg.project_root / "data" / "processed"
        run_day = datetime.now(timezone.utc).date().isoformat()
        
        final_results = []
        for res in results:
            slug = sanitize_filename_part(res.profile.display_name)
            date_range_str = f"{start_date}_to_{end_date}" if start_date and end_date else run_day
            stem = f"{slug}_{date_range_str}_{report_type}"
            out_dir = processed_dir / stem
            export_dataframe(res.wide, out_dir, stem=stem, long_df=res.long_daily)
            final_results.append({
                "profile": res.profile.display_name,
                "csv_name": f"{stem}/{stem}.csv",
                "xlsx_name": f"{stem}/{stem}.xlsx",
                "run_id": res.run_id
            })
        
        _jobs[job_id]["status"] = "success"
        _jobs[job_id]["message"] = f"Export complete. {len(final_results)} report(s) generated."
        _jobs[job_id]["results"] = final_results
    except Exception as e:
        debug_log(f"[JOB {job_id}] EXCEPTION: {e}")
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["message"] = str(e)

@app.post("/api/fetch-bulk")
async def fetch_bulk(request: BulkFetchRequest):
    """Starts an export job in the background and returns a job_id immediately."""
    job_id = _uuid.uuid4().hex[:12]
    _jobs[job_id] = {
        "status": "pending",
        "message": "Job queued...",
        "results": [],
        "report_type": request.report_type,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    
    t = threading.Thread(
        target=_run_export_job,
        args=(job_id, request.ids, request.report_type, request.start_date, request.end_date),
        daemon=True,
    )
    t.start()
    
    debug_log(f"Started background job {job_id} for {request.report_type}")
    return {"status": "accepted", "job_id": job_id}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Poll for a background job's status."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/analytics/ranges")
async def get_range_analytics():
    try:
        app_cfg = load_app_config()
        ranges_dir = app_cfg.project_root / "ranges"
        processed_dir = app_cfg.project_root / "data" / "processed"
        
        if not ranges_dir.exists():
            return {"ranges": [], "subcategories": [], "total_asins": 0}
        
        csv_files = list(ranges_dir.glob("*.csv"))
        if not csv_files:
            return {"ranges": [], "subcategories": [], "total_asins": 0}
        
        range_df = pd.read_csv(csv_files[0])
        range_df['Asins'] = range_df['Asins'].astype(str).str.strip()
        
        performance_files = list(processed_dir.glob("**/*_spProducts.csv"))
        if performance_files:
            latest_perf = max(performance_files, key=lambda x: x.stat().st_mtime)
            perf_df = pd.read_csv(latest_perf)
            
            spend_cols = [c for c in perf_df.columns if c.startswith('spend_')]
            sales_cols = [c for c in perf_df.columns if c.startswith('sales_')]
            
            perf_df['total_spend'] = perf_df[spend_cols].sum(axis=1)
            perf_df['total_sales'] = perf_df[sales_cols].sum(axis=1)
            
            merged = pd.merge(range_df, perf_df[['asin', 'total_spend', 'total_sales']], 
                             left_on='Asins', right_on='asin', how='left')
            
            range_analytics = merged.groupby('Ranges').agg({
                'Asins': 'count',
                'total_spend': 'sum',
                'total_sales': 'sum'
            }).reset_index()
            
            range_analytics['roas'] = range_analytics['total_sales'] / range_analytics['total_spend']
            range_analytics = range_analytics.fillna(0)
            
            subcat_analytics = merged.groupby('Subcat').agg({
                'Asins': 'count',
                'total_spend': 'sum',
                'total_sales': 'sum'
            }).reset_index()
            
            return {
                "ranges": range_analytics.rename(columns={'Asins': 'count'}).to_dict('records'),
                "subcategories": subcat_analytics.rename(columns={'Asins': 'count'}).to_dict('records'),
                "total_asins": len(range_df)
            }
        
        range_counts = range_df.groupby('Ranges').size().reset_index(name='count').to_dict('records')
        subcat_counts = range_df.groupby('Subcat').size().reset_index(name='count').to_dict('records')
        
        return {
            "ranges": range_counts,
            "subcategories": subcat_counts,
            "total_asins": len(range_df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
