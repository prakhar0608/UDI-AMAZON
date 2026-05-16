
import os
import sys
import time
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path("src")))

from amazon_ads_app.config import load_app_config
from amazon_ads_app.profile_discovery import discover_all_profiles
from amazon_ads_app.auth import LwaTokenProvider
from amazon_ads_app.api_client import AdsApiClient

def main():
    try:
        app = load_app_config()
        print("Config loaded successfully.")
        
        tp = LwaTokenProvider(
            app.lwa_client_id,
            app.lwa_client_secret,
            app.lwa_refresh_token
        )
        
        print("Discovering profiles...")
        profiles, errors = discover_all_profiles(app, tp)
        print(f"Found {len(profiles)} profiles.")
        
        if not profiles:
            print("No profiles found. Cannot proceed with report test.")
            return

        # Pick the first profile
        profile = profiles[0]
        print(f"\nTesting profile: {profile.display_name} (ID: {profile.id}, Region: {profile.region})")
        
        with AdsApiClient(
            base_url="https://advertising-api.amazon.com" if profile.region == "NA" else "https://advertising-api-eu.amazon.com",
            client_id=app.lwa_client_id,
            token_provider=tp,
            profile_id=profile.id
        ) as client:
            print("Checking profile eligibility via /v2/profiles (scoped)...")
            r = client.request("GET", "/v2/profiles")
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                print("Profile access verified.")
            else:
                print(f"Failed to verify profile: {r.text}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
