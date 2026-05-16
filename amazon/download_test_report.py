
import sys
from pathlib import Path
import logging
import time

# Add src to sys.path
sys.path.append(str(Path("src")))

from amazon_ads_app.config import load_app_config, ProfileConfig
from amazon_ads_app.auth import LwaTokenProvider
from amazon_ads_app.api_client import AdsApiClient
from amazon_ads_app.reports_v3 import get_report_status, download_report_url, decompress_if_gzip
from amazon_ads_app.parse_report import parse_report_payload

logging.basicConfig(level=logging.INFO)

def check_and_download(report_id):
    try:
        app_cfg = load_app_config()
        tp = LwaTokenProvider(
            app_cfg.lwa_client_id,
            app_cfg.lwa_client_secret,
            app_cfg.lwa_refresh_token,
        )
        
        profile_id = 2021853942333200 # shoprythm CA
        base_url = "https://advertising-api.amazon.com"
        
        with AdsApiClient(base_url, app_cfg.lwa_client_id, tp, profile_id=profile_id) as client:
            for _ in range(20):
                status = get_report_status(client, report_id)
                curr_status = (status.get("status") or status.get("processingStatus") or "").upper()
                print(f"Status: {curr_status}")
                if curr_status in ("COMPLETED", "SUCCESS"):
                    url = status.get("url") or (status.get("location") if isinstance(status.get("location"), str) else None)
                    if not url and isinstance(status.get("completionDetails"), dict):
                        url = status["completionDetails"].get("url")
                    
                    if url:
                        print("Downloading report...")
                        raw_bytes = download_report_url(url)
                        df = parse_report_payload(raw_bytes)
                        print(f"Parsed {len(df)} rows.")
                        print(f"Columns: {df.columns.tolist()}")
                        if not df.empty:
                            print("Sample data:")
                            print(df.head(5))
                        return
                elif curr_status in ("FAILURE", "FAILED"):
                    print(f"Report failed: {status}")
                    return
                time.sleep(15)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_and_download("30bb2344-009c-426c-bd6e-7a54bf8fa345")
