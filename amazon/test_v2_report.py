
import sys
from pathlib import Path
import logging

# Add src to sys.path
sys.path.append(str(Path("src")))

from amazon_ads_app.config import load_app_config, ProfileConfig
from amazon_ads_app.auth import LwaTokenProvider
from amazon_ads_app.api_client import AdsApiClient

logging.basicConfig(level=logging.INFO)

def test_v2_report():
    try:
        app_cfg = load_app_config()
        token_provider = LwaTokenProvider(
            app_cfg.lwa_client_id,
            app_cfg.lwa_client_secret,
            app_cfg.lwa_refresh_token,
        )
        
        # profile_id = 3327926123185661 # BR
        profile_id = 2021853942333200 # CA
        base_url = "https://advertising-api.amazon.com"
        
        print(f"Testing V2 report for profile {profile_id}...")
        
        with AdsApiClient(base_url, app_cfg.lwa_client_id, token_provider, profile_id=profile_id) as client:
            # V2 SP AD report
            body = {
                "reportDate": "2026-05-12",
                "metrics": "impressions,clicks,cost,attributedSales7d"
            }
            r = client.request("POST", "/v2/sp/ad/report", json=body)
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_v2_report()
