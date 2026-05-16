
import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path("src")))

# Load .env explicitly if needed, but load_app_config does it
from amazon_ads_app.config import load_app_config
from amazon_ads_app.profile_discovery import discover_all_profiles
from amazon_ads_app.auth import LwaTokenProvider

def main():
    try:
        app = load_app_config()
        print("Config loaded successfully.")
        
        tp = LwaTokenProvider(
            app.lwa_client_id,
            app.lwa_client_secret,
            app.lwa_refresh_token
        )
        
        print("Attempting to refresh token...")
        token = tp.get_access_token()
        print(f"Token refreshed successfully. Length: {len(token)}")
        
        print("Discovering profiles...")
        profiles, errors = discover_all_profiles(app, tp)
        
        print(f"Found {len(profiles)} profiles.")
        if errors:
            print("Errors encountered:")
            for reg, err in errors.items():
                print(f"  {reg}: {err}")
        
        if profiles:
            print("\nFirst 5 profiles:")
            for p in profiles[:5]:
                print(f"  - {p.display_name} (ID: {p.id}, Region: {p.region})")
        else:
            print("No profiles found.")
                
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
