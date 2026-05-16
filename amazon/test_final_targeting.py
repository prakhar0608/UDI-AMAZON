
import sys
from pathlib import Path
import logging

# Add src to sys.path
sys.path.append(str(Path("src")))

from amazon_ads_app.config import load_app_config, ProfileConfig
from amazon_ads_app.auth import LwaTokenProvider
from amazon_ads_app.api_client import AdsApiClient
from amazon_ads_app.reports_v3 import create_sp_daily_report

logging.basicConfig(level=logging.INFO)

def test_final_targeting_logic():
    try:
        app_cfg = load_app_config()
        tp = LwaTokenProvider(
            app_cfg.lwa_client_id,
            app_cfg.lwa_client_secret,
            app_cfg.lwa_refresh_token,
        )
        
        profile_id = 2021853942333200 # shoprythm CA
        base_url = "https://advertising-api.amazon.com"
        
        print(f"Testing FINAL targeting logic for profile {profile_id}...")
        
        with AdsApiClient(base_url, app_cfg.lwa_client_id, tp, profile_id=profile_id) as client:
            report_id = create_sp_daily_report(
                client,
                name="final-targeting-test",
                start_date="2026-05-10",
                end_date="2026-05-12",
                report_type="spTargeting"
            )
            print(f"Report ID: {report_id}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_final_targeting_logic()
