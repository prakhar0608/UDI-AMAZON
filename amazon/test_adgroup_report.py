
import sys
from pathlib import Path
import logging

# Add src to sys.path
sys.path.append(str(Path("src")))

from amazon_ads_app.config import load_app_config, ProfileConfig
from amazon_ads_app.auth import LwaTokenProvider
from amazon_ads_app.api_client import AdsApiClient

logging.basicConfig(level=logging.INFO)

def test_adgroup_report():
    try:
        app_cfg = load_app_config()
        tp = LwaTokenProvider(
            app_cfg.lwa_client_id,
            app_cfg.lwa_client_secret,
            app_cfg.lwa_refresh_token,
        )
        
        profile_id = 2021853942333200 # shoprythm CA
        base_url = "https://advertising-api.amazon.com"
        
        print(f"Testing adgroup report for profile {profile_id}...")
        
        with AdsApiClient(base_url, app_cfg.lwa_client_id, tp, profile_id=profile_id) as client:
            body = {
                "name": "test-adgroup-v3",
                "startDate": "2026-05-10",
                "endDate": "2026-05-12",
                "configuration": {
                    "adProduct": "SPONSORED_PRODUCTS",
                    "groupBy": ["advertiser"],
                    "columns": ["date", "campaignId", "adGroupId", "impressions", "clicks", "cost"],
                    "reportTypeId": "spCampaigns",
                    "timeUnit": "DAILY",
                    "format": "GZIP_JSON",
                },
            }
            r = client.request("POST", "/reporting/reports", json=body)
            print(f"Create status: {r.status_code}")
            print(f"Response: {r.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_adgroup_report()
